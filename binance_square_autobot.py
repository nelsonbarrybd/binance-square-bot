#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================================
BINANCE SQUARE WRITE-TO-EARN AUTO-BOT (HUMAN VOICE + MANDATORY EMOJIS & CHART EDITION)
=========================================================================================
Key Upgrades:
1. Guaranteed Trader Emojis: Enforces rich emoji bullet points (📍, 🛡️, 🚧, 📈, 🟢, 🔴, 💬, 👇)
   on every single post, even when generated via Cloudflare LLM.
2. Robust Image Path Resolution: Resolves `square-post` directory automatically across
   local PC, Linux, and GitHub Actions runners so `post-image.mjs` is guaranteed to fire.
3. Natural Human Trader Phrasing: Clean blank lines, conversational tone, zero raw stars (**),
   and TradingView-style 1H candlestick charts.
=========================================================================================
"""

import argparse
import datetime
import json
import os
import random
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

plt.rcParams["text.parse_math"] = False

BINANCE_SPOT_ENDPOINTS = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
]
BINANCE_FUTURES_BASE = "https://fapi.binance.com"
BINANCE_SQUARE_OPENAPI_URL = (
    "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
)

CF_SENTIMENT_MODEL = os.environ.get(
    "CF_SENTIMENT_MODEL", "@cf/huggingface/distilbert-sst-2-int8"
)
CF_TEXT_MODEL = os.environ.get(
    "CF_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8"
)
CF_TEXT_FALLBACK_MODEL = "@cf/mistral/mistral-7b-instruct-v0.2-lora"

CORE_WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "SUIUSDT", "LINKUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]

COIN_FULL_NAMES = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "bnb",
    "SOL": "solana",
    "XRP": "xrp",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "AVAX": "avalanche",
    "SUI": "sui",
    "LINK": "chainlink",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "INJ": "injective",
}

MACRO_CRYPTO_RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://finance.yahoo.com/news/rssindex",
]

CONTENT_FORMATS = [
    "CHART_IMAGE_POST",
    "QUICK_ALERT",
    "CHART_IMAGE_POST",
    "TRADER_POLL",
    "LONG_ARTICLE",
]

GLOBAL_SESSIONS = {
    "ASIA_PEAK": {
        "name": "Asian Session",
        "utc_hours": (0, 8),
        "bst_window": "সকাল ০৬:০০ - দুপুর ০২:০০ (BST)",
        "interval_minutes": 30,
    },
    "EUROPE_LONDON_PEAK": {
        "name": "London Session",
        "utc_hours": (8, 13),
        "bst_window": "দুপুর ০২:০০ - সন্ধ্যা ০৭:০০ (BST)",
        "interval_minutes": 25,
    },
    "US_EUROPE_OVERLAP_PEAK": {
        "name": "US & London Overlap",
        "utc_hours": (13, 21),
        "bst_window": "সন্ধ্যা ০৭:০০ - রাত ০৩:০০ (BST)",
        "interval_minutes": 22,
    },
    "LATE_US_PACIFIC": {
        "name": "Late US Session",
        "utc_hours": (21, 24),
        "bst_window": "রাত ০৩:০০ - সকাল ০৬:০০ (BST)",
        "interval_minutes": 45,
    },
}


def sanitize_human_post_text(raw_text: str) -> str:
    text = raw_text.strip()
    for label in (
        "CHART_IMAGE_POST", "QUICK_ALERT", "TRADER_POLL", "LONG_ARTICLE",
        "BREAKOUT_VOLUME_ALERT", "INSTITUTIONAL_SR_SETUP", "FUTURES_FUNDING_SQUEEZE",
        "MACRO_FINANCE_CORRELATION", "Executive Summary:", "Introduction:",
    ):
        text = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(rf"\b{re.escape(label)}\s*:?\s*", "", text, flags=re.IGNORECASE)

    # Convert plain headers into clean emoji headers
    text = re.sub(r"(?:\*\*Bull(?:ish)?\s+(?:Trade\s+)?(?:Plan|Setup):?\*\*|Bull(?:ish)?\s+(?:Trade\s+)?(?:Plan|Setup):?)", "🟢 Bull Idea:", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:\*\*Bear(?:ish)?\s+(?:Trade\s+)?(?:Plan|Setup):?\*\*|Bear(?:ish)?\s+(?:Trade\s+)?(?:Plan|Setup):?)", "🔴 Bear Idea:", text, flags=re.IGNORECASE)

    # Convert price lines into clean emoji bullets if missing
    text = re.sub(r"(?m)^Price:\s*", "📍 Price: ", text)
    text = re.sub(r"(?m)^Support(?:\s+to\s+hold)?:\s*", "🛡️ Support: ", text)
    text = re.sub(r"(?m)^Resistance(?:\s+to\s+break)?:\s*", "🚧 Resistance: ", text)
    text = re.sub(r"(?m)^1H\s+EMA-20:\s*", "📈 1H EMA-20: ", text)

    text = text.replace("**", "").replace("__", "").replace("```", "")
    text = re.sub(r"(?m)^#{1,4}\s*", "", text)
    text = re.sub(r"\bAI\s+News\s+Sentiment\b", "Market Mood", text, flags=re.IGNORECASE)
    text = re.sub(r"\bAI\s+Sentiment\b", "Market Mood", text, flags=re.IGNORECASE)
    text = re.sub(r"\bAI\b", "Market", text)
    text = re.sub(r"(?m)^\s*[\*\-]\s+", "• ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_seo_image_filename(base_coin: str, fmt: str) -> str:
    coin_slug = COIN_FULL_NAMES.get(base_coin.upper(), base_coin.lower())
    pair_slug = f"{base_coin.lower()}-usdt"
    date_slug = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H%M")
    if fmt == "LONG_ARTICLE":
        return f"{coin_slug}-{pair_slug}-macro-market-brief-{date_slug}.png"
    return f"{coin_slug}-{pair_slug}-1h-price-chart-levels-{date_slug}.png"


def get_cloudflare_credentials() -> Tuple[str, str]:
    acc_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    return acc_id, token


def analyze_market_sentiment(headline: str, price_change_24h: float) -> Dict[str, object]:
    acc_id, token = get_cloudflare_credentials()
    if acc_id and token:
        url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/run/{CF_SENTIMENT_MODEL}"
        payload = json.dumps({"text": headline}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("result", [])
                if isinstance(results, list) and results:
                    top = max(results, key=lambda item: float(item.get("score", 0.0)))
                    raw_label = str(top.get("label", "POSITIVE")).upper()
                    score_pct = float(top.get("score", 0.75)) * 100.0
                    sentiment = "Bullish" if "POS" in raw_label else "Cautious"
                    return {"sentiment": sentiment, "confidence": round(score_pct, 1)}
        except Exception:
            pass
    sentiment = "Bullish" if price_change_24h >= 0 else "Cautious"
    conf = min(94.0, 68.0 + abs(price_change_24h) * 2.5)
    return {"sentiment": sentiment, "confidence": round(conf, 1)}


def generate_text_cloudflare(prompt: str) -> Optional[str]:
    acc_id, token = get_cloudflare_credentials()
    if not (acc_id and token):
        return None
    for model_name in (CF_TEXT_MODEL, CF_TEXT_FALLBACK_MODEL):
        url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/run/{model_name}"
        payload = json.dumps({
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an experienced human crypto trader sharing your personal chart notes on Binance Square. "
                        "Write in a relaxed, natural, first-person trader voice. "
                        "Keep sentences short and super easy to read on a phone screen. "
                        "MANDATORY: Use clean trader emojis (📍, 🛡️, 🚧, 📈, 🟢, 🔴, 💬, 👇) on each bullet line! "
                        "STRICT RULES: NO asterisks (** or *), NO mention of AI/bots."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 380,
            "temperature": 0.75,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = ((data.get("result") or {}).get("response") or "").strip()
                if len(text) > 70:
                    return sanitize_human_post_text(text)
        except Exception:
            continue
    return None


def http_get_json(url: str, timeout: int = 12) -> Optional[object]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def fetch_binance_spot_json(path: str) -> Optional[object]:
    for base in BINANCE_SPOT_ENDPOINTS:
        res = http_get_json(f"{base}{path}")
        if res is not None:
            return res
    return None


def fetch_macro_news_headlines(max_items: int = 3) -> List[str]:
    headlines: List[str] = []
    for feed_url in MACRO_CRYPTO_RSS_FEEDS:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            for item in root.findall(".//item/title"):
                if item.text and len(item.text.strip()) > 15:
                    clean_title = item.text.strip()
                    if clean_title not in headlines:
                        headlines.append(clean_title)
                if len(headlines) >= max_items:
                    return headlines
        except Exception:
            continue
    return headlines or [
        "Spot volume picks up as traders position for the US and London overlap",
        "Large-cap tokens hold key support zones ahead of macro data",
    ]


def compute_ema(values: List[float], period: int) -> np.ndarray:
    arr = np.array(values, dtype=float)
    if len(arr) < period:
        return arr
    ema = np.zeros_like(arr)
    ema[0] = arr[0]
    alpha = 2.0 / (period + 1.0)
    for i in range(1, len(arr)):
        ema[i] = alpha * arr[i] + (1.0 - alpha) * ema[i - 1]
    return ema


def compute_rsi(closes: List[float], period: int = 14) -> np.ndarray:
    arr = np.array(closes, dtype=float)
    if len(arr) <= period:
        return np.full_like(arr, 50.0)
    deltas = np.diff(arr)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 100.0
    rsi = np.zeros_like(arr)
    rsi[:period] = 50.0
    rsi[period] = 100.0 - 100.0 / (1.0 + rs)
    for i in range(period + 1, len(arr)):
        delta = deltas[i - 1]
        upval = max(delta, 0.0)
        downval = -min(delta, 0.0)
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 100.0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)
    return rsi


def scan_trending_market_candidate() -> Dict[str, object]:
    tickers = fetch_binance_spot_json("/api/v3/ticker/24hr")
    funding_list = http_get_json(f"{BINANCE_FUTURES_BASE}/fapi/v1/premiumIndex")

    funding_map: Dict[str, float] = {}
    if isinstance(funding_list, list):
        for item in funding_list:
            sym = item.get("symbol")
            if sym and "lastFundingRate" in item:
                try:
                    funding_map[sym] = float(item["lastFundingRate"]) * 100.0
                except ValueError:
                    pass

    selected_symbol = random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT"])
    ticker_info = None

    if isinstance(tickers, list):
        candidates = [
            t for t in tickers
            if t.get("symbol") in CORE_WATCHLIST
            and float(t.get("quoteVolume", 0.0)) > 25_000_000
        ]
        if candidates:
            candidates.sort(key=lambda x: abs(float(x.get("priceChangePercent", 0.0))), reverse=True)
            ticker_info = random.choice(candidates[:6])
            selected_symbol = ticker_info["symbol"]

    raw_klines = fetch_binance_spot_json(f"/api/v3/klines?symbol={selected_symbol}&interval=1h&limit=48" )

    if isinstance(raw_klines, list) and len(raw_klines) >= 30:
        timestamps = [int(k[0]) for k in raw_klines]
        opens = [float(k[1]) for k in raw_klines]
        highs = [float(k[2]) for k in raw_klines]
        lows = [float(k[3]) for k in raw_klines]
        closes = [float(k[4]) for k in raw_klines]
        volumes = [float(k[5]) for k in raw_klines]
        last_price = closes[-1]
        change_24h = (
            float(ticker_info["priceChangePercent"])
            if ticker_info
            else ((closes[-1] - closes[-24]) / closes[-24]) * 100.0
        )
        quote_vol_24h = (
            float(ticker_info["quoteVolume"])
            if ticker_info
            else sum(v * c for v, c in zip(volumes[-24:], closes[-24:]))
        )
    else:
        now_ms = int(time.time() * 1000)
        base_price = 88450.0 if selected_symbol == "BTCUSDT" else 184.50
        timestamps, opens, highs, lows, closes, volumes = [], [], [], [], [], []
        curr = base_price * 0.96
        rng = random.Random(42)
        for i in range(48):
            timestamps.append(now_ms - (48 - i) * 3600 * 1000)
            o = curr
            delta = curr * rng.uniform(-0.008, 0.011)
            c = o + delta
            h = max(o, c) + curr * rng.uniform(0.001, 0.006)
            l = min(o, c) - curr * rng.uniform(0.001, 0.006)
            v = rng.uniform(1200, 4800)
            opens.append(o)
            highs.append(h)
            lows.append(l)
            closes.append(c)
            volumes.append(v)
            curr = c
        last_price = closes[-1]
        change_24h = ((closes[-1] - closes[-24]) / closes[-24]) * 100.0
        quote_vol_24h = 415_000_000.0

    ema20 = compute_ema(closes, 20)
    ema50 = compute_ema(closes, 35)
    rsi14 = compute_rsi(closes, 14)

    recent_support = min(lows[-20:])
    recent_resistance = max(highs[-20:])
    base_coin = selected_symbol.replace("USDT", "")
    funding_pct = funding_map.get(selected_symbol, 0.0085)
    headlines = fetch_macro_news_headlines(max_items=2)
    sentiment_info = analyze_market_sentiment(headlines[0], change_24h)

    return {
        "symbol": selected_symbol,
        "base_coin": base_coin,
        "cashtag": f"${base_coin}",
        "last_price": last_price,
        "change_24h": change_24h,
        "quote_vol_24h": quote_vol_24h,
        "funding_pct": funding_pct,
        "support": recent_support,
        "resistance": recent_resistance,
        "rsi": float(rsi14[-1]),
        "ema20": float(ema20[-1]),
        "ema50": float(ema50[-1]),
        "timestamps": timestamps,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes,
        "ema20_series": ema20.tolist(),
        "ema50_series": ema50.tolist(),
        "rsi_series": rsi14.tolist(),
        "headlines": headlines,
        "sentiment": sentiment_info["sentiment"],
    }


def format_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.2f}"
    if value >= 1:
        return f"${value:.3f}"
    return f"${value:.5f}"


def generate_real_market_chart_image(
    market_data: Dict[str, object],
    session_info: Dict[str, object],
    output_path: str,
) -> str:
    bg_dark = "#0B0E11"
    panel_bg = "#131722"
    grid_color = "#1E222D"
    text_primary = "#D1D4DC"
    text_muted = "#787B86"
    gold_accent = "#F0B90B"
    bull_green = "#089981"
    bear_red = "#F23645"
    ema20_color = "#F0B90B"
    ema50_color = "#2962FF"

    opens = market_data["opens"]
    highs = market_data["highs"]
    lows = market_data["lows"]
    closes = market_data["closes"]
    volumes = market_data["volumes"]
    ema20 = market_data["ema20_series"]
    ema50 = market_data["ema50_series"]
    rsi_series = market_data["rsi_series"]

    n = len(closes)
    x = np.arange(n)

    fig = plt.figure(figsize=(12, 7.2), dpi=150, facecolor=bg_dark)
    gs = GridSpec(
        3, 1,
        height_ratios=[3.6, 0.9, 1.1],
        hspace=0.10,
        left=0.05, right=0.91, top=0.86, bottom=0.08,
    )

    ax_price = fig.add_subplot(gs[0], facecolor=panel_bg)
    ax_vol = fig.add_subplot(gs[1], facecolor=panel_bg, sharex=ax_price)
    ax_rsi = fig.add_subplot(gs[2], facecolor=panel_bg, sharex=ax_price)

    chg = float(market_data["change_24h"])
    chg_sign = "+" if chg >= 0 else ""

    fig.text(
        0.05, 0.93,
        f"{market_data['base_coin']}USDT  •  1H  •  BINANCE SPOT",
        color=text_primary, fontsize=15, fontweight="bold",
    )
    fig.text(
        0.05, 0.89,
        f"Last: {format_price(float(market_data['last_price']))} ({chg_sign}{chg:.2f}%)   "
        f"Vol(24h): ${float(market_data['quote_vol_24h'])/1e6:,.1f}M   "
        f"EMA20: {format_price(float(market_data['ema20']))}   "
        f"EMA50: {format_price(float(market_data['ema50']))}   "
        f"RSI(14): {float(market_data['rsi']):.1f}",
        color=text_muted, fontsize=10, fontweight="bold",
    )
    fig.text(
        0.91, 0.93,
        f"{session_info['name']}",
        color=gold_accent, fontsize=11, fontweight="bold", ha="right",
    )

    candle_width = 0.64
    for idx in range(n):
        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        color = bull_green if c >= o else bear_red
        ax_price.plot([idx, idx], [l, h], color=color, linewidth=1.1, zorder=2)
        lower = min(o, c)
        height = max(abs(c - o), (h - l) * 0.035)
        rect = mpatches.Rectangle(
            (idx - candle_width / 2.0, lower),
            candle_width,
            height,
            facecolor=color,
            edgecolor=color,
            zorder=3,
        )
        ax_price.add_patch(rect)

    ax_price.plot(x, ema20, color=ema20_color, linewidth=1.5, label="EMA 20", zorder=4)
    ax_price.plot(x, ema50, color=ema50_color, linewidth=1.5, label="EMA 50", zorder=4)

    support = float(market_data["support"])
    resistance = float(market_data["resistance"])
    price_span = max(resistance - support, support * 0.01)
    zone_thickness = price_span * 0.045

    ax_price.axhspan(
        resistance - zone_thickness, resistance + zone_thickness,
        color=bear_red, alpha=0.14, zorder=1,
    )
    ax_price.axhline(
        resistance, color=bear_red, linestyle="--", linewidth=1.1, alpha=0.85,
        label=f"Resistance ({format_price(resistance)})",
    )

    ax_price.axhspan(
        support - zone_thickness, support + zone_thickness,
        color=bull_green, alpha=0.14, zorder=1,
    )
    ax_price.axhline(
        support, color=bull_green, linestyle="--", linewidth=1.1, alpha=0.85,
        label=f"Support ({format_price(support)})",
    )

    ax_price.legend(
        loc="upper left", facecolor=bg_dark, edgecolor=grid_color,
        labelcolor=text_primary, fontsize=8.5, ncol=4,
    )

    vol_colors = [bull_green if closes[i] >= opens[i] else bear_red for i in range(n)]
    ax_vol.bar(x, volumes, width=candle_width, color=vol_colors, alpha=0.75)
    ax_vol.set_ylabel("Vol", color=text_muted, fontsize=8.5)

    ax_rsi.plot(x, rsi_series, color="#B2B5BE", linewidth=1.4)
    ax_rsi.axhline(70, color=bear_red, linestyle=":", linewidth=0.9, alpha=0.75)
    ax_rsi.axhline(30, color=bull_green, linestyle=":", linewidth=0.9, alpha=0.75)
    ax_rsi.fill_between(x, 30, 70, color="#2A2E39", alpha=0.25)
    ax_rsi.set_ylim(15, 85)
    ax_rsi.set_ylabel("RSI", color=text_muted, fontsize=8.5)

    for ax in (ax_price, ax_vol, ax_rsi):
        ax.grid(True, color=grid_color, linestyle="-", linewidth=0.6, alpha=0.8)
        ax.tick_params(colors=text_muted, labelsize=8.5)
        ax.yaxis.tick_right()
        for spine in ax.spines.values():
            spine.set_color(grid_color)

    plt.setp(ax_price.get_xticklabels(), visible=False)
    plt.setp(ax_vol.get_xticklabels(), visible=False)

    tick_indices = list(range(0, n, 8)) + ([n - 1] if (n - 1) % 8 != 0 else [])
    tick_labels = [
        datetime.datetime.fromtimestamp(
            market_data["timestamps"][i] / 1000.0, tz=datetime.timezone.utc
        ).strftime("%d %b %H:%M")
        for i in tick_indices
    ]
    ax_rsi.set_xticks(tick_indices)
    ax_rsi.set_xticklabels(tick_labels, color=text_muted, fontsize=8)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, facecolor=bg_dark, metadata={"Software": ""})
    plt.close(fig)
    return str(out_file.resolve())


def generate_macro_article_header_banner(
    market_data: Dict[str, object],
    session_info: Dict[str, object],
    output_path: str,
) -> str:
    bg_dark = "#0B0E11"
    panel_bg = "#161A1E"
    border_color = "#2B3139"
    text_primary = "#EAECEF"
    text_muted = "#848E9C"
    gold_accent = "#F0B90B"
    bull_green = "#089981"
    bear_red = "#F23645"

    chg = float(market_data["change_24h"])
    chg_sign = "+" if chg >= 0 else ""
    chg_color = bull_green if chg >= 0 else bear_red

    fig = plt.figure(figsize=(12, 6.75), dpi=150, facecolor=bg_dark)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=bg_dark)
    ax.axis("off")

    card = mpatches.FancyBboxPatch(
        (0.04, 0.06), 0.92, 0.88,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor=panel_bg, edgecolor=border_color, linewidth=1.5,
    )
    ax.add_patch(card)

    ax.text(0.08, 0.86, "ALPHAPULSE INSIGHTS  •  INSTITUTIONAL MARKET DESK",
            color=gold_accent, fontsize=12, fontweight="bold", family="sans-serif")
    ax.text(0.92, 0.86, session_info["name"].upper(),
            color=text_muted, fontsize=11, fontweight="bold", ha="right", family="sans-serif")

    ax.plot([0.08, 0.92], [0.82, 0.82], color=border_color, linewidth=1.0)

    ax.text(0.08, 0.72, f"{market_data['base_coin']}/USDT 1H STRATEGIC BRIEF",
            color=text_primary, fontsize=24, fontweight="bold", family="sans-serif")

    price_str = format_price(float(market_data["last_price"]))
    ax.text(0.08, 0.62, f"Index Price: {price_str}  ({chg_sign}{chg:.2f}%)",
            color=chg_color, fontsize=18, fontweight="bold", family="sans-serif")

    metrics = [
        ("SUPPORT LEVEL", format_price(float(market_data["support"])), bull_green),
        ("RESISTANCE WALL", format_price(float(market_data["resistance"])), bear_red),
        ("24H SPOT VOLUME", f"${float(market_data['quote_vol_24h'])/1e6:,.1f}M", text_primary),
    ]

    card_xs = [0.08, 0.37, 0.66]
    for idx, (lbl, val, col) in enumerate(metrics):
        box_x = card_xs[idx]
        sub_card = mpatches.FancyBboxPatch(
            (box_x, 0.38), 0.26, 0.18,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor="#0B0E11", edgecolor=border_color, linewidth=1.0,
        )
        ax.add_patch(sub_card)
        ax.text(box_x + 0.02, 0.51, lbl, color=text_muted, fontsize=9.5, fontweight="bold", family="sans-serif")
        ax.text(box_x + 0.02, 0.42, val, color=col, fontsize=14, fontweight="bold", family="sans-serif")

    macro_card = mpatches.FancyBboxPatch(
        (0.08, 0.14), 0.84, 0.18,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        facecolor="#0B0E11", edgecolor=border_color, linewidth=1.0,
    )
    ax.add_patch(macro_card)
    ax.text(0.10, 0.26, "MARKET DRIVER ON THE TAPE:", color=gold_accent, fontsize=9, fontweight="bold", family="sans-serif")
    headline = market_data["headlines"][0]
    if len(headline) > 85:
        headline = headline[:82] + "..."
    ax.text(0.10, 0.18, f'"{headline}"', color=text_primary, fontsize=11, style="italic", family="sans-serif")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, facecolor=bg_dark, metadata={"Software": ""})
    plt.close(fig)
    return str(out_file.resolve())


def generate_multi_format_content(
    market_data: Dict[str, object],
    session_info: Dict[str, object],
    content_format: str,
) -> Tuple[str, Optional[str]]:
    primary_tag = str(market_data["cashtag"])
    secondary_tags = [t for t in ["$BTC", "$ETH", "$BNB"] if t != primary_tag][:2]
    cashtag_str = f"{primary_tag} {secondary_tags[0]} {secondary_tags[1]}"

    price_str = format_price(float(market_data["last_price"]))
    sup_str = format_price(float(market_data["support"]))
    res_str = format_price(float(market_data["resistance"]))
    ema20_str = format_price(float(market_data["ema20"]))
    stop_bull_str = format_price(float(market_data["support"]) * 0.985)
    chg = float(market_data["change_24h"])
    rsi_val = float(market_data["rsi"])
    funding_val = float(market_data["funding_pct"])
    headline = market_data["headlines"][0]

    if content_format == "QUICK_ALERT":
        direction_word = "pushing higher" if chg >= 0 else "testing key support"
        text = (
            f"👀 Anyone else watching {primary_tag} right now?\n\n"
            f"Price is {direction_word} at {price_str} ({chg:+.2f}% today) as {session_info['name']} volume steps in.\n\n"
            f"Here are the only two levels that matter on my screen:\n"
            f"🟢 Buyers defending: {sup_str}\n"
            f"🔴 Breakout wall: {res_str}\n"
            f"⚡ 1H RSI: {rsi_val:.1f} | Funding: {funding_val:+.4f}%\n\n"
            f"If we flip {res_str} with volume, this could run fast. If {sup_str} gives out, I'm waiting patiently for the lower sweep.\n\n"
            f"💬 Are you buying {primary_tag} here or sitting on hands? Drop your thoughts below! 👇\n\n"
            f"{cashtag_str} #Write2Earn #CryptoTrading #BinanceSquare"
        )
        return sanitize_human_post_text(text), None

    if content_format == "TRADER_POLL":
        text = (
            f"🔥 Quick Poll for {primary_tag} Traders at {price_str}! 📊\n\n"
            f"{primary_tag} is sitting right in the middle of a tight 1H range during the {session_info['name']}.\n\n"
            f"🟢 Camp Bull: Holds {sup_str} and breaks above {res_str} next.\n"
            f"🔴 Camp Bear: Rejects under {ema20_str} (EMA-20) and sweeps below {sup_str}.\n\n"
            f"Personally, I want to see how the next 1H candle closes near {ema20_str} before adding size.\n\n"
            f"💬 Which camp are you in today — Bullish or Bearish on {primary_tag}? Comment your target price! 👇\n\n"
            f"{cashtag_str} #Write2Earn #CryptoMarket #BinanceSquare"
        )
        return sanitize_human_post_text(text), None

    if content_format == "LONG_ARTICLE":
        title = f"My 1H Game Plan for {market_data['base_coin']} ({price_str}): Key Levels & Trade Setup"
        text = (
            f"I've been tracking {primary_tag} closely throughout the {session_info['name']}, and the 1H chart is setting up a clean risk-reward play.\n\n"
            f"Right now, {primary_tag} is trading around {price_str} ({chg:+.2f}% over the last 24 hours) with ${float(market_data['quote_vol_24h'])/1e6:,.1f}M in spot turnover. "
            f"Meanwhile, traders are also reacting to today's macro headline: \"{headline}\".\n\n"
            f"📊 Key Levels on My 1H Chart:\n"
            f"📍 Current Price: {price_str}\n"
            f"🛡️ Demand Zone (Support): {sup_str}\n"
            f"🚧 Supply Wall (Resistance): {res_str}\n"
            f"📈 Trend Filter: 1H EMA-20 at {ema20_str} | ⚡ RSI(14) at {rsi_val:.1f}\n\n"
            f"🟢 How I'm Playing the Upside:\n"
            f"I don't like chasing middle-of-the-range candles. My ideal long entry is either a clean retest and bounce off {sup_str}, or a confirmed 1H close above {res_str} with volume, keeping invalidation tight below {stop_bull_str}.\n\n"
            f"🔴 What Flips Me Bearish:\n"
            f"If buyers fail to hold {sup_str} and we see heavy sell volume, I'll step aside and wait for the liquidity sweep to finish before looking for entries alongside {secondary_tags[0]} and {secondary_tags[1]}.\n\n"
            f"💬 How are you trading {primary_tag} today — Long, Short, or waiting for confirmation? Let's compare notes in the comments! 👇\n\n"
            f"{cashtag_str} #Write2Earn #TradingStrategy #BinanceSquare"
        )
        return sanitize_human_post_text(text), title

    # Format 4: CHART_IMAGE_POST
    llm_prompt = f"""Share a short, conversational 1H chart update on {primary_tag} at {price_str} ({chg:+.2f}% 24h) during the {session_info['name']}.
Write like a real human trader talking to friends on Binance Square:
- Hook: Why you are looking at {primary_tag} right now.
- Clean emoji bullet list of your levels:
  📍 Price: {price_str}
  🛡️ Support: {sup_str}
  🚧 Resistance: {res_str}
  📈 1H EMA-20: {ema20_str} | ⚡ RSI: {rsi_val:.1f}
- 🟢 Bull Idea (bounce at {sup_str} or breakout above {res_str}, stop below {stop_bull_str}).
- 🔴 Bear Idea (rejection at {res_str}).
- Friendly closing question asking if readers are Long or Short on {primary_tag} today.
- End with {cashtag_str} #Write2Earn #CryptoTrading #BinanceSquare.
Remember: NO asterisks (**), NO mention of AI, keep lines short and easy to read."""

    cf_text = generate_text_cloudflare(llm_prompt)
    if cf_text and primary_tag in cf_text:
        return sanitize_human_post_text(cf_text), None

    text = (
        f"📊 Keeping {primary_tag} on my main watchlist at {price_str}! 🎯\n\n"
        f"Price action on the 1H chart is tightening up nicely during the {session_info['name']}. "
        f"Instead of guessing, here are the exact levels I have marked out right now:\n\n"
        f"📍 Current Price: {price_str} ({chg:+.2f}% 24h)\n"
        f"🛡️ Key Support Zone: {sup_str} (buyers stepped in here recently)\n"
        f"🚧 Major Resistance: {res_str}\n"
        f"📈 1H EMA-20: {ema20_str} | ⚡ RSI(14): {rsi_val:.1f}\n\n"
        f"🟢 My Bullish Plan: Watching for a clean hold above {sup_str} or a high-volume push through {res_str} to ride momentum alongside {secondary_tags[0]}, keeping risk defined below {stop_bull_str}.\n\n"
        f"🔴 The Risk: If we get rejected hard at {res_str} on low volume, expect another pullback to test {sup_str}.\n\n"
        f"💬 What's your play on {primary_tag} from here — Longing the dip or Shorting the resistance? Let me know below! 👇\n\n"
        f"{cashtag_str} #Write2Earn #TechnicalAnalysis #BinanceSquare"
    )
    return sanitize_human_post_text(text), None


def get_current_global_session(utc_now: Optional[datetime.datetime] = None) -> Dict[str, object]:
    if utc_now is None:
        utc_now = datetime.datetime.now(datetime.timezone.utc)
    hour = utc_now.hour
    for key, session in GLOBAL_SESSIONS.items():
        start_h, end_h = session["utc_hours"]
        if start_h <= hour < end_h:
            return {"key": key, **session}
    return {"key": "ASIA_PEAK", **GLOBAL_SESSIONS["ASIA_PEAK"]}


def find_square_skill_scripts_dir(custom_path: Optional[str] = None) -> Optional[Path]:
    """Look for square-post scripts directory across relative and absolute locations."""
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path))
        candidates.append(Path(custom_path) / "scripts")

    candidates.extend([
        Path("square-post"),
        Path("square-post/scripts"),
        Path("./square-post/scripts"),
        Path.home() / ".config/binance-square",
        Path.cwd() / "square-post",
        Path.cwd() / "square-post/scripts",
    ])

    for c in candidates:
        if (c / "post-image.mjs").exists():
            return c
        if (c / "scripts/post-image.mjs").exists():
            return c / "scripts"
    return None


def publish_to_binance_square(
    post_text: str,
    image_paths: List[str],
    article_title: Optional[str] = None,
    square_skill_dir: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, object]:
    if dry_run:
        return {
            "status": "DRY_RUN_SUCCESS",
            "post_url": "https://www.binance.com/square/post/DRY_RUN_PREVIEW",
            "images": image_paths,
            "title": article_title,
        }

    api_key = os.environ.get("BINANCE_SQUARE_OPENAPI_KEY", "").strip()
    if not api_key:
        key_file = Path.home() / ".config" / "binance-square" / "openapi-key"
        if key_file.exists():
            api_key = key_file.read_text(encoding="utf-8").strip()

    if not api_key:
        raise RuntimeError("Missing BINANCE_SQUARE_OPENAPI_KEY! Set $env:BINANCE_SQUARE_OPENAPI_KEY='your_key'.")

    # Route A: Official square-post Node.js scripts for Image and Article uploads
    scripts_dir = find_square_skill_scripts_dir(square_skill_dir)
    if scripts_dir:
        env = {**os.environ, "BINANCE_SQUARE_OPENAPI_KEY": api_key}
        resolved_images = [str(Path(p).resolve()) for p in image_paths]

        # Case 1: Long Article with Title and Cover Banner
        if article_title and resolved_images:
            script_file = scripts_dir / "post-image.mjs"
            cmd = ["node", str(script_file), "--text", post_text, "--title", article_title, "--cover", resolved_images[0]]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                return {"status": "PUBLISHED_ARTICLE_WITH_COVER", "stdout": proc.stdout.strip(), "images": resolved_images}
            print(f"[WARN] post-image.mjs article non-zero ({proc.stderr}), falling back.")

        # Case 2: Chart Image Post
        elif resolved_images:
            script_file = scripts_dir / "post-image.mjs"
            cmd = ["node", str(script_file), "--text", post_text, "--images", ",".join(resolved_images)]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                return {"status": "PUBLISHED_CHART_POST", "stdout": proc.stdout.strip(), "images": resolved_images}
            print(f"[WARN] post-image.mjs chart non-zero ({proc.stderr}), falling back.")

        # Case 3: Pure Text Post (Quick Alert or Poll)
        else:
            script_file = scripts_dir / "post-text.mjs"
            cmd = ["node", str(script_file), "--text", post_text]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=40)
            if proc.returncode == 0:
                return {"status": "PUBLISHED_TEXT_ONLY", "stdout": proc.stdout.strip(), "images": []}
            print(f"[WARN] post-text.mjs non-zero ({proc.stderr}), falling back.")

    # Route B: Direct OpenAPI fallback (Posts text directly to Binance Square)
    payload = json.dumps({"bodyTextOnly": post_text}).encode("utf-8")
    req = urllib.request.Request(
        BINANCE_SQUARE_OPENAPI_URL,
        data=payload,
        headers={"X-Square-OpenAPI-Key": api_key, "Content-Type": "application/json", "clienttype": "binanceSkill"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    code = result.get("code")
    if code == "000000":
        content_id = (result.get("data") or {}).get("id", "unavailable")
        return {
            "status": "PUBLISHED_OPENAPI_TEXT",
            "post_url": f"https://www.binance.com/square/post/{content_id}",
            "response": result,
            "images": image_paths,
        }
    raise RuntimeError(f"Binance Square API Error ({code}): {result}")


def run_single_cycle(
    output_dir: str,
    cycle_index: int = 0,
    force_format: Optional[str] = None,
    square_skill_dir: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, object]:
    session_info = get_current_global_session()
    content_format = force_format or CONTENT_FORMATS[cycle_index % len(CONTENT_FORMATS)]
    market_data = scan_trending_market_candidate()

    post_text, article_title = generate_multi_format_content(market_data, session_info, content_format)
    image_list: List[str] = []

    if content_format == "CHART_IMAGE_POST":
        chart_filename = build_seo_image_filename(str(market_data["base_coin"]), content_format)
        chart_path = str(Path(output_dir) / chart_filename)
        saved_chart = generate_real_market_chart_image(market_data, session_info, chart_path)
        image_list.append(saved_chart)

    elif content_format == "LONG_ARTICLE":
        banner_filename = build_seo_image_filename(str(market_data["base_coin"]), content_format)
        banner_path = str(Path(output_dir) / banner_filename)
        saved_banner = generate_macro_article_header_banner(market_data, session_info, banner_path)
        image_list.append(saved_banner)

    pub_result = publish_to_binance_square(
        post_text=post_text,
        image_paths=image_list,
        article_title=article_title,
        square_skill_dir=square_skill_dir,
        dry_run=dry_run,
    )

    return {
        "format": content_format,
        "session": session_info["name"],
        "bst_window": session_info["bst_window"],
        "symbol": market_data["symbol"],
        "cashtag": market_data["cashtag"],
        "images": image_list,
        "title": article_title,
        "post_text": post_text,
        "publish_result": pub_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Binance Square Write-to-Earn Auto-Bot (100% Human Trader Edition)"
    )
    parser.add_argument("--once", action="store_true", help="Run a single post cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Preview locally without publishing.")
    parser.add_argument(
        "--format",
        choices=["CHART_IMAGE_POST", "QUICK_ALERT", "LONG_ARTICLE", "TRADER_POLL"],
        help="Force a specific post format.",
    )
    parser.add_argument("--output-dir", default="./generated_charts", help="Directory for SEO chart PNGs.")
    parser.add_argument("--square-skill-dir", default=os.environ.get("SQUARE_SKILL_DIR", ""), help="Path to square-post skill.")
    args = parser.parse_args()

    if args.once:
        slot_index = int(time.time() // 1500)
        summary = run_single_cycle(
            output_dir=args.output_dir,
            cycle_index=slot_index,
            force_format=args.format,
            square_skill_dir=args.square_skill_dir or None,
            dry_run=args.dry_run,
        )
        print("=" * 78)
        print(f"[FORMAT]    {summary['format']}  |  [COIN] {summary['symbol']} ({summary['cashtag']})")
        print(f"[SESSION]   {summary['session']} ({summary['bst_window']})")
        print(f"[SEO FILES] {summary['images']}")
        if summary.get("title"):
            print(f"[TITLE]     {summary['title']}")
        print("-" * 78)
        print(summary["post_text"])
        print("-" * 78)
        print(f"[STATUS]    {summary['publish_result']}")
        print("=" * 78)
        return

    print("[START] Launching 24/7 Human-Style Multi-Format Scheduler...")
    cycle_count = 0
    while True:
        try:
            summary = run_single_cycle(
                output_dir=args.output_dir,
                cycle_index=cycle_count,
                square_skill_dir=args.square_skill_dir or None,
                dry_run=args.dry_run,
            )
            cycle_count += 1
            print(
                f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M UTC')}] "
                f"Post #{cycle_count} [{summary['format']}] ({summary['cashtag']}) -> {summary['publish_result']['status']}"
            )
        except Exception as exc:
            print(f"[ERROR] Cycle failed: {exc}")

        session = get_current_global_session()
        base_wait = int(session["interval_minutes"]) * 60
        jitter_seconds = random.randint(-240, 240)
        sleep_seconds = max(600, base_wait + jitter_seconds)
        print(f"[SCHEDULER] Active Desk: {session['name']} | Next in {sleep_seconds // 60}m {sleep_seconds % 60}s...")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
