#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BINANCE SQUARE WRITE-TO-EARN AUTO-BOT V4.0 (VIRAL HUMAN & ENGAGEMENT ENGINE)
File Name: binance_square_autobot.py
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
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.gridspec import GridSpec
import numpy as np

plt.rcParams["text.parse_math"] = False


def clean_url(raw_url: str) -> str:
    u = str(raw_url).strip()
    m = re.search(r"\((https?://[^\s\)\]]+)\)", u)
    if m:
        u = m.group(1)
    u = u.replace("[", "").replace("]", "").replace(" ", "")
    return u


SCHEME = "https" + "://"
BINANCE_SPOT_ENDPOINTS = [
    SCHEME + ".".join(["data-api", "binance", "vision"]),
    SCHEME + ".".join(["api", "binance", "com"]),
]
BINANCE_FUTURES_BASE = SCHEME + ".".join(["fapi", "binance", "com"])
BINANCE_SQUARE_OPENAPI_URL = (
    SCHEME + ".".join(["www", "binance", "com"]) + "/bapi/composite/v1/public/pgc/openApi/content/add"
)
CF_API_HOST = SCHEME + ".".join(["api", "cloudflare", "com"])
TG_API_HOST = SCHEME + ".".join(["api", "telegram", "org"])
SQUARE_POST_BASE_URL = SCHEME + ".".join(["www", "binance", "com"]) + "/square/post/"

CF_TEXT_MODEL = os.environ.get(
    "CF_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8"
)
CF_TEXT_FALLBACK_MODEL = "@cf/mistral/mistral-7b-instruct-v0.2-lora"
CF_IMAGE_MODEL = os.environ.get(
    "CF_IMAGE_MODEL", "@cf/bytedance/stable-diffusion-xl-lightning"
)

ZERO_COMMISSION_BLACKLIST = {
    "USDC", "FDUSD", "USDT", "TUSD", "BUSD", "DAI", "USDP", "USDE", "PYUSD",
    "EUR", "EURI", "AEUR", "TRY", "BRL", "JPY", "GBP", "AUD", "RUB", "UAH",
    "PAXG", "WBTC", "WBETH", "BETH", "BTTC", "WIN", "SHIB1000", "1000SHIB",
    "1000PEPE", "1000BONK", "1000FLOKI", "1000SATS", "1000RATS", "1000CAT",
    "BTCDOM", "DEFI", "XUSD", "USD1",
}

HIGH_COMMISSION_MAJORS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "PEPEUSDT", "SUIUSDT", "ADAUSDT", "AVAXUSDT",
    "LINKUSDT", "TRUMPUSDT", "WIFUSDT", "SHIBUSDT", "NEARUSDT",
    "APTUSDT", "FETUSDT", "RENDERUSDT", "INJUSDT", "ARBUSDT",
    "OPUSDT", "TONUSDT", "TIAUSDT", "TAOUSDT", "AAVEUSDT",
    "UNIUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT", "FILUSDT",
    "PENDLEUSDT", "ENAUSDT", "ONDOUSDT", "JUPUSDT", "ZECUSDT",
]

COIN_SEO_SLUGS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "bnb",
    "XRP": "xrp", "DOGE": "dogecoin", "PEPE": "pepe-coin", "SUI": "sui",
    "ADA": "cardano", "AVAX": "avalanche", "LINK": "chainlink",
    "TRUMP": "official-trump", "WIF": "dogwifhat", "SHIB": "shiba-inu",
    "NEAR": "near-protocol", "APT": "aptos", "FET": "artificial-superintelligence",
    "RENDER": "render-token", "INJ": "injective", "ARB": "arbitrum",
    "OP": "optimism", "TON": "toncoin", "TIA": "celestia", "TAO": "bittensor",
    "AAVE": "aave", "UNI": "uniswap", "ZEC": "zcash", "ENA": "ethena",
    "ONDO": "ondo-finance", "PENDLE": "pendle", "JUP": "jupiter",
}

VISUAL_FORMATS = [
    "MOBILE_ARROW_CHART",
    "PRO_SETUP_BOX_CHART",
    "VOLATILITY_SHOCK_CARD",
    "TRADER_POLL",
    "CHEAT_SHEET_ALPHA",
    "DUAL_COMBO_POST",
]

HUMAN_PERSONAS = [
    {
        "id": "LIQUIDITY_HUNT_TRADER",
        "name": "Smart Money Orderflow Sniper",
        "angle": "Explain where trapped breakout traders or panic sellers gave liquidity to spot whales.",
    },
    {
        "id": "FUNDING_ARBITRAGE_ANALYST",
        "name": "Perp Derivatives Specialist",
        "angle": "Call out retail over-leverage, perpetual funding imbalance, and short squeeze risk.",
    },
    {
        "id": "LEVEL_TO_LEVEL_SCALPER",
        "name": "Intraday Price Action Tape Reader",
        "angle": "Ultra-crisp 3-sentence read focusing strictly on the rejection wick, EMA-20, and the invalidation point.",
    },
    {
        "id": "CONTRARIAN_SHOCK_REALIST",
        "name": "Anti-FOMO Market Realist",
        "angle": "Directly challenge retail excitement or panic. Tell them why chasing green/red candles here is suicidal.",
    },
    {
        "id": "RANGE_ROTATION_STRATEGIST",
        "name": "Institutional Range Architect",
        "angle": "Outline the exact supply ceiling vs demand base without taking emotional sides.",
    },
]

GLOBAL_SESSIONS = {
    "ASIA_PEAK": {
        "name": "Asian Session",
        "utc_hours": (0, 8),
        "interval_minutes": 180,  # 3 hours spacing
    },
    "EUROPE_LONDON_PEAK": {
        "name": "London Session",
        "utc_hours": (8, 13),
        "interval_minutes": 150,  # 2.5 hours spacing
    },
    "US_EUROPE_OVERLAP_PEAK": {
        "name": "US & London Overlap",
        "utc_hours": (13, 21),
        "interval_minutes": 140,  # Prime liquidity spacing
    },
    "LATE_US_PACIFIC": {
        "name": "Late US & Daily Close",
        "utc_hours": (21, 24),
        "interval_minutes": 210,  # 3.5 hours spacing
    },
}


def load_bot_memory(memory_file: str) -> Dict[str, List[str]]:
    path = Path(memory_file)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "recent_coins": list(data.get("recent_coins", []))[-12:],
                "recent_personas": list(data.get("recent_personas", []))[-6:],
                "recent_formats": list(data.get("recent_formats", []))[-4:],
            }
        except Exception:
            pass
    return {"recent_coins": [], "recent_personas": [], "recent_formats": []}


def save_bot_memory(
    memory_file: str,
    memory: Dict[str, List[str]],
    coin: str,
    persona_id: str,
    fmt: str,
) -> None:
    memory["recent_coins"] = (memory.get("recent_coins", []) + [coin])[-12:]
    memory["recent_personas"] = (memory.get("recent_personas", []) + [persona_id])[-6:]
    memory["recent_formats"] = (memory.get("recent_formats", []) + [fmt])[-4:]
    path = Path(memory_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def sanitize_human_post_text(raw_text: str) -> str:
    text = raw_text.strip()

    # রোবোটিক হেডার এবং এআই বয়ান ক্লিনিং
    for label in (
        "MOBILE_ARROW_CHART", "PRO_SETUP_BOX_CHART", "PURE_TEXT_ALPHA",
        "DUAL_COMBO_POST", "VOLATILITY_SHOCK_CARD", "TRADER_POLL",
        "CHEAT_SHEET_ALPHA", "Executive Summary:", "Market Overview:",
    ):
        text = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", text, flags=re.IGNORECASE)

    # এআই-এর মুখস্থ গ্রিটিংস ফিল্টার
    text = re.sub(
        r"^(?:Hey|Hi|Hello|Yo|What's up|Greetings)\s+"
        r"(?:guys|friends|traders|everyone|squad|fam|team|folks|crypto fam)"
        r"(?:\s+on\s+Binance\s+Square)?[\s,!.\-—👋👀🔥]*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^(?:Quick\s+update|Just\s+checking\s+in|Taking\s+a\s+quick\s+look|Let's\s+talk\s+about)\s*(?:on|at)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # চার্টের রঙ নির্দেশকারী অপ্রয়োজনীয় বাক্য বাদ
    text = re.sub(r"\b[Tt]he\s+(?:red|green)\s+(?:chart\s+)?arrow\s+points\s+toward\b", "Momentum shifts toward", text)
    text = re.sub(r"\b[Tt]he\s+(?:red|green)\s+(?:chart\s+)?arrow\b", "the 1H structure", text)

    # কাঠখোট্টা ট্রানজিশন শব্দ বাদ
    text = re.sub(r"\b(?:Furthermore|Moreover|In conclusion|To summarize|As we can see|It is worth noting),?\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(r"(\$[A-Z0-9]{2,10})\s+([,.:;!?])", r"\1\2", text)
    text = re.sub(r"(\$[A-Z0-9]{2,10})\s*/\s*USDT", r"\1", text)
    text = re.sub(r"(\$[A-Z0-9]{2,10})\s+'s\b", r"\1's", text)

    text = text.replace("**", "").replace("__", "").replace("```", "").replace('"', "")
    text = re.sub(r"(?m)^#{1,4}\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_seo_image_filename(base_coin: str, fmt: str, suffix: str = "chart") -> str:
    coin_slug = COIN_SEO_SLUGS.get(base_coin.upper(), base_coin.lower())
    pair_slug = f"{base_coin.lower()}-usdt"
    date_slug = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H%M")
    return f"{coin_slug}-{pair_slug}-{fmt.lower().replace('_', '-')}-{suffix}-{date_slug}.png"


def http_get_json(url: str, timeout: int = 12) -> Optional[object]:
    try:
        safe_u = clean_url(url)
        req = urllib.request.Request(
            safe_u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
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


def is_commission_eligible_symbol(symbol: str, valid_spot_symbols: set) -> bool:
    if not symbol.endswith("USDT"):
        return False
    if symbol not in valid_spot_symbols:
        return False
    base = symbol[:-4]
    if base in ZERO_COMMISSION_BLACKLIST:
        return False
    if not base.isalpha() or not (2 <= len(base) <= 9):
        return False
    for bad_suffix in ("UP", "DOWN", "BULL", "BEAR"):
        if base.endswith(bad_suffix) and base != "JUP":
            return False
    return True


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


def scan_trending_market_candidate(recent_coins: List[str]) -> Dict[str, object]:
    spot_tickers = fetch_binance_spot_json("/api/v3/ticker/24hr")
    futures_tickers = http_get_json(f"{BINANCE_FUTURES_BASE}/fapi/v1/ticker/24hr")
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

    valid_spot_map: Dict[str, dict] = {}
    if isinstance(spot_tickers, list):
        for t in spot_tickers:
            sym = str(t.get("symbol", ""))
            vol = float(t.get("quoteVolume", 0.0))
            if sym.endswith("USDT") and vol >= 15_000_000:
                valid_spot_map[sym] = t

    valid_spot_symbols = set(valid_spot_map.keys())
    eligible_pool: List[dict] = []

    if isinstance(futures_tickers, list) and valid_spot_symbols:
        for ft in futures_tickers:
            sym = str(ft.get("symbol", ""))
            if not is_commission_eligible_symbol(sym, valid_spot_symbols):
                continue
            f_vol = float(ft.get("quoteVolume", 0.0))
            if f_vol < 35_000_000:
                continue
            eligible_pool.append(valid_spot_map[sym])

    if not eligible_pool and valid_spot_map:
        for sym, st in valid_spot_map.items():
            if is_commission_eligible_symbol(sym, valid_spot_symbols):
                eligible_pool.append(st)

    fresh_pool = [
        t for t in eligible_pool
        if t["symbol"].replace("USDT", "") not in recent_coins
    ]
    if not fresh_pool:
        fresh_pool = eligible_pool

    selected_symbol = "SOLUSDT"
    ticker_info = None

    if fresh_pool:
        fresh_pool.sort(key=lambda x: abs(float(x.get("priceChangePercent", 0.0))), reverse=True)
        top_movers = fresh_pool[:8]
        major_movers = [t for t in fresh_pool if t["symbol"] in HIGH_COMMISSION_MAJORS]

        if major_movers and random.random() < 0.45:
            major_movers.sort(key=lambda x: abs(float(x.get("priceChangePercent", 0.0))), reverse=True)
            ticker_info = random.choice(major_movers[:6])
        else:
            ticker_info = random.choice(top_movers)
        selected_symbol = ticker_info["symbol"]
    else:
        fallback_choices = [s for s in HIGH_COMMISSION_MAJORS if s.replace("USDT", "") not in recent_coins]
        selected_symbol = random.choice(fallback_choices or HIGH_COMMISSION_MAJORS[:6])

    raw_klines = fetch_binance_spot_json(f"/api/v3/klines?symbol={selected_symbol}&interval=1h&limit=48")

    if isinstance(raw_klines, list) and len(raw_klines) >= 30:
        timestamps = [int(k[0]) for k in raw_klines]
        opens = [float(k[1]) for k in raw_klines]
        highs = [float(k[2]) for k in raw_klines]
        lows = [float(k[3]) for k in raw_klines]
        closes = [float(k[4]) for k in raw_klines]
        volumes = [float(k[5]) for k in raw_klines]
        last_price = closes[-1]
        high_24h = max(highs[-24:])
        low_24h = min(lows[-24:])
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
        raise RuntimeError(f"Unable to fetch live Binance klines for {selected_symbol}")

    ema20 = compute_ema(closes, 20)
    ema50 = compute_ema(closes, 35)
    rsi14 = compute_rsi(closes, 14)

    recent_support = min(lows[-18:])
    recent_resistance = max(highs[-18:])
    base_coin = selected_symbol.replace("USDT", "")
    funding_pct = funding_map.get(selected_symbol, 0.0095)

    dist_to_res = abs(recent_resistance - last_price)
    dist_to_sup = abs(last_price - recent_support)
    is_bullish_bias = (
        (change_24h >= 1.5 and float(rsi14[-1]) < 70)
        or (float(rsi14[-1]) <= 34)
        or (last_price >= float(ema20[-1]) and dist_to_sup < dist_to_res)
    )
    bias_label = "BULLISH" if is_bullish_bias else "BEARISH"
    target_price = recent_resistance if is_bullish_bias else recent_support

    return {
        "symbol": selected_symbol,
        "base_coin": base_coin,
        "cashtag": f"${base_coin}",
        "last_price": last_price,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "change_24h": change_24h,
        "quote_vol_24h": quote_vol_24h,
        "funding_pct": funding_pct,
        "support": recent_support,
        "resistance": recent_resistance,
        "target_price": target_price,
        "rsi": float(rsi14[-1]),
        "ema20": float(ema20[-1]),
        "ema50": float(ema50[-1]),
        "bias": bias_label,
        "timestamps": timestamps,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes,
        "ema20_series": ema20.tolist(),
        "ema50_series": ema50.tolist(),
        "rsi_series": rsi14.tolist(),
    }


def format_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.2f}"
    if value >= 10:
        return f"${value:.2f}"
    if value >= 1:
        return f"${value:.3f}"
    if value >= 0.01:
        return f"${value:.4f}"
    if value >= 0.0001:
        return f"${value:.6f}"
    return f"${value:.8f}"


def generate_mobile_arrow_chart(
    market_data: Dict[str, object],
    output_path: str,
) -> str:
    bg_dark = "#11151C"
    panel_bg = "#161B24"
    grid_color = "#222936"
    text_primary = "#EAECEF"
    text_muted = "#848E9C"
    bull_green = "#0ECB81"
    bear_red = "#F6465D"
    ma7_color = "#F0B90B"
    ma25_color = "#C93B86"

    opens = market_data["opens"][-32:]
    highs = market_data["highs"][-32:]
    lows = market_data["lows"][-32:]
    closes = market_data["closes"][-32:]
    volumes = market_data["volumes"][-32:]
    ema20 = market_data["ema20_series"][-32:]
    ema50 = market_data["ema50_series"][-32:]

    n = len(closes)
    x = np.arange(n)

    fig = plt.figure(figsize=(8.0, 10.0), dpi=150, facecolor=bg_dark)
    gs = GridSpec(
        2, 1,
        height_ratios=[4.2, 1.0],
        hspace=0.06,
        left=0.06, right=0.88, top=0.77, bottom=0.07,
    )

    ax_price = fig.add_subplot(gs[0], facecolor=panel_bg)
    ax_vol = fig.add_subplot(gs[1], facecolor=panel_bg, sharex=ax_price)

    chg = float(market_data["change_24h"])
    chg_sign = "+" if chg >= 0 else ""
    price_col = bull_green if chg >= 0 else bear_red
    last_p = float(market_data["last_price"])

    fig.text(0.06, 0.93, f"{market_data['base_coin']}USDT", color=text_primary, fontsize=22, fontweight="bold")
    fig.text(0.34, 0.935, "Perp", color="#F0B90B", fontsize=12, fontweight="bold")
    fig.text(0.06, 0.86, format_price(last_p).replace("$", ""), color=price_col, fontsize=26, fontweight="bold")
    fig.text(
        0.06, 0.815,
        f"≈ {format_price(last_p)}   {chg_sign}{chg:.2f}%",
        color=price_col, fontsize=13, fontweight="bold",
    )

    fig.text(0.58, 0.91, "24h High", color=text_muted, fontsize=10)
    fig.text(0.88, 0.91, format_price(float(market_data["high_24h"])).replace("$", ""), color=text_primary, fontsize=10, ha="right")
    fig.text(0.58, 0.87, "24h Low", color=text_muted, fontsize=10)
    fig.text(0.88, 0.87, format_price(float(market_data["low_24h"])).replace("$", ""), color=text_primary, fontsize=10, ha="right")
    fig.text(0.58, 0.83, "24h Vol(USDT)", color=text_muted, fontsize=10)
    fig.text(0.88, 0.83, f"{float(market_data['quote_vol_24h'])/1e6:,.1f}M", color=text_primary, fontsize=10, ha="right")

    candle_width = 0.62
    for idx in range(n):
        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        color = bull_green if c >= o else bear_red
        ax_price.plot([idx, idx], [l, h], color=color, linewidth=1.3, zorder=2)
        lower = min(o, c)
        height = max(abs(c - o), (h - l) * 0.04)
        rect = mpatches.Rectangle(
            (idx - candle_width / 2.0, lower),
            candle_width,
            height,
            facecolor=color,
            edgecolor=color,
            zorder=3,
        )
        ax_price.add_patch(rect)

    ax_price.plot(x, ema20, color=ma7_color, linewidth=1.6, label="EMA(20)", zorder=4)
    ax_price.plot(x, ema50, color=ma25_color, linewidth=1.6, label="EMA(50)", zorder=4)

    support = float(market_data["support"])
    resistance = float(market_data["resistance"])
    span = max(resistance - support, last_p * 0.02)

    ax_price.set_xlim(-1, n + 6)
    ax_price.set_ylim(support - span * 0.22, resistance + span * 0.25)

    ax_price.axhline(support, color=bull_green, linestyle="--", linewidth=1.1, alpha=0.7)
    ax_price.axhline(resistance, color=bear_red, linestyle="--", linewidth=1.1, alpha=0.7)

    is_bull = market_data["bias"] == "BULLISH"
    arrow_color = bull_green if is_bull else bear_red
    target_y = (resistance + span * 0.12) if is_bull else (support - span * 0.12)
    rad_curve = -0.25 if is_bull else 0.25

    arrow = FancyArrowPatch(
        (n - 1, last_p),
        (n + 4.2, target_y),
        connectionstyle=f"arc3,rad={rad_curve}",
        arrowstyle="->,head_length=18,head_width=14",
        color=arrow_color,
        linewidth=5.0,
        zorder=10,
    )
    ax_price.add_patch(arrow)

    label_txt = f"TARGET: {format_price(resistance if is_bull else support)}"
    ax_price.text(
        n + 4.0,
        target_y + (span * 0.05 if is_bull else -span * 0.07),
        label_txt,
        color="#FFFFFF",
        fontsize=10.5,
        fontweight="bold",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.35", facecolor=arrow_color, edgecolor="none", alpha=0.92),
        zorder=11,
    )

    vol_colors = [bull_green if closes[i] >= opens[i] else bear_red for i in range(n)]
    ax_vol.bar(x, volumes, width=candle_width, color=vol_colors, alpha=0.8)

    for ax in (ax_price, ax_vol):
        ax.grid(True, color=grid_color, linestyle="-", linewidth=0.6, alpha=0.75)
        ax.tick_params(colors=text_muted, labelsize=9)
        ax.yaxis.tick_right()
        for spine in ax.spines.values():
            spine.set_color(grid_color)

    plt.setp(ax_price.get_xticklabels(), visible=False)
    plt.setp(ax_vol.get_xticklabels(), visible=False)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, facecolor=bg_dark, metadata={"Software": ""})
    plt.close(fig)
    return str(out_file.resolve())


def generate_pro_setup_box_chart(
    market_data: Dict[str, object],
    session_info: Dict[str, object],
    output_path: str,
) -> str:
    bg_dark = "#0B0E11"
    panel_bg = "#131722"
    grid_color = "#1E222D"
    text_primary = "#D1D4DC"
    text_muted = "#787B86"
    bull_green = "#089981"
    bear_red = "#F23645"

    opens = market_data["opens"]
    highs = market_data["highs"]
    lows = market_data["lows"]
    closes = market_data["closes"]
    rsi_series = market_data["rsi_series"]
    ema20 = market_data["ema20_series"]

    n = len(closes)
    x = np.arange(n)

    fig = plt.figure(figsize=(12, 7.2), dpi=150, facecolor=bg_dark)
    gs = GridSpec(2, 1, height_ratios=[3.8, 1.1], hspace=0.08, left=0.05, right=0.90, top=0.86, bottom=0.08)

    ax_price = fig.add_subplot(gs[0], facecolor=panel_bg)
    ax_rsi = fig.add_subplot(gs[1], facecolor=panel_bg, sharex=ax_price)

    chg = float(market_data["change_24h"])
    last_p = float(market_data["last_price"])
    sup = float(market_data["support"])
    res = float(market_data["resistance"])
    is_bull = market_data["bias"] == "BULLISH"

    fig.text(
        0.05, 0.92,
        f"{market_data['base_coin']}USDT  •  1H R:R SETUP  •  {session_info['name'].upper()}",
        color=text_primary, fontsize=15, fontweight="bold",
    )
    fig.text(
        0.05, 0.88,
        f"Spot: {format_price(last_p)} ({chg:+.2f}%)   |   Support: {format_price(sup)}   |   "
        f"Resistance: {format_price(res)}   |   1H RSI: {float(market_data['rsi']):.1f}",
        color=text_muted, fontsize=10.5, fontweight="bold",
    )

    candle_width = 0.64
    for idx in range(n):
        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        color = bull_green if c >= o else bear_red
        ax_price.plot([idx, idx], [l, h], color=color, linewidth=1.1, zorder=2)
        rect = mpatches.Rectangle(
            (idx - candle_width / 2.0, min(o, c)),
            candle_width,
            max(abs(c - o), (h - l) * 0.035),
            facecolor=color, edgecolor=color, zorder=3,
        )
        ax_price.add_patch(rect)

    ax_price.plot(x, ema20, color="#F0B90B", linewidth=1.5, label="1H EMA 20", zorder=4)

    box_start = n - 2
    box_width = 6.5
    if is_bull:
        tp_level = res
        sl_level = sup * 0.988
        profit_box = mpatches.Rectangle(
            (box_start, last_p), box_width, max(tp_level - last_p, last_p * 0.01),
            facecolor=bull_green, edgecolor=bull_green, alpha=0.24, zorder=5,
        )
        stop_box = mpatches.Rectangle(
            (box_start, sl_level), box_width, max(last_p - sl_level, last_p * 0.005),
            facecolor=bear_red, edgecolor=bear_red, alpha=0.24, zorder=5,
        )
    else:
        tp_level = sup
        sl_level = res * 1.012
        profit_box = mpatches.Rectangle(
            (box_start, tp_level), box_width, max(last_p - tp_level, last_p * 0.01),
            facecolor=bull_green, edgecolor=bull_green, alpha=0.24, zorder=5,
        )
        stop_box = mpatches.Rectangle(
            (box_start, last_p), box_width, max(sl_level - last_p, last_p * 0.005),
            facecolor=bear_red, edgecolor=bear_red, alpha=0.24, zorder=5,
        )

    ax_price.add_patch(profit_box)
    ax_price.add_patch(stop_box)
    ax_price.set_xlim(-1, n + 6)

    ax_rsi.plot(x, rsi_series, color="#B2B5BE", linewidth=1.4)
    ax_rsi.axhline(70, color=bear_red, linestyle=":", linewidth=0.9)
    ax_rsi.axhline(30, color=bull_green, linestyle=":", linewidth=0.9)
    ax_rsi.set_ylim(15, 85)
    ax_rsi.set_ylabel("RSI", color=text_muted, fontsize=8.5)

    for ax in (ax_price, ax_rsi):
        ax.grid(True, color=grid_color, linestyle="-", linewidth=0.6, alpha=0.8)
        ax.tick_params(colors=text_muted, labelsize=8.5)
        ax.yaxis.tick_right()
        for spine in ax.spines.values():
            spine.set_color(grid_color)

    plt.setp(ax_price.get_xticklabels(), visible=False)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, facecolor=bg_dark, metadata={"Software": ""})
    plt.close(fig)
    return str(out_file.resolve())


def generate_volatility_shock_card(
    market_data: Dict[str, object],
    output_path: str,
) -> str:
    bg_dark = "#0B0E11"
    panel_bg = "#151921"
    bull_green = "#0ECB81"
    bear_red = "#F6465D"
    gold = "#F0B90B"
    text_white = "#FFFFFF"
    text_muted = "#848E9C"

    chg = float(market_data["change_24h"])
    is_bull = market_data["bias"] == "BULLISH"
    accent = bull_green if chg >= 0 else bear_red
    bias_col = bull_green if is_bull else bear_red

    fig = plt.figure(figsize=(10, 8), dpi=150, facecolor=bg_dark)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=bg_dark)
    ax.axis("off")

    card = mpatches.FancyBboxPatch(
        (0.05, 0.06), 0.90, 0.88,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor=panel_bg, edgecolor=accent, linewidth=2.2,
    )
    ax.add_patch(card)

    tag_title = "MOMENTUM BREAKOUT WATCH" if is_bull else "SELL-SIDE PRESSURE / TRAP ALERT"
    ax.text(0.09, 0.86, f"BINANCE FUTURES & SPOT  •  {tag_title}", color=gold, fontsize=12, fontweight="bold")
    ax.text(0.09, 0.75, f"${market_data['base_coin']} / USDT", color=text_white, fontsize=30, fontweight="bold")

    price_str = format_price(float(market_data["last_price"]))
    ax.text(0.09, 0.64, f"{price_str}  ({chg:+.2f}%)", color=accent, fontsize=24, fontweight="bold")

    zones = [
        ("BUYER DEMAND ZONE", format_price(float(market_data["support"])), bull_green),
        ("SELLER SUPPLY WALL", format_price(float(market_data["resistance"])), bear_red),
        ("24H TURNOVER", f"${float(market_data['quote_vol_24h'])/1e6:,.1f}M", text_white),
        ("CHART TARGET", format_price(float(market_data["target_price"])), bias_col),
    ]

    xs = [0.09, 0.52, 0.09, 0.52]
    ys = [0.40, 0.40, 0.16, 0.16]
    for i, (lbl, val, col) in enumerate(zones):
        box = mpatches.FancyBboxPatch(
            (xs[i], ys[i]), 0.38, 0.17,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor="#0B0E11", edgecolor="#2B3139", linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(xs[i] + 0.03, ys[i] + 0.11, lbl, color=text_muted, fontsize=10.5, fontweight="bold")
        ax.text(xs[i] + 0.03, ys[i] + 0.035, val, color=col, fontsize=17, fontweight="bold")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, facecolor=bg_dark, metadata={"Software": ""})
    plt.close(fig)
    return str(out_file.resolve())


def generate_cloudflare_reaction_visual(
    base_coin: str, bias: str, output_path: str
) -> Optional[str]:
    acc_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not (acc_id and token):
        return None

    try:
        url = clean_url(f"{CF_API_HOST}/client/v4/accounts/{acc_id}/ai/run/{CF_IMAGE_MODEL}")
        scene = (
            f"dramatic 3D financial illustration of a glowing golden crypto bull charging upward through green candlesticks for {base_coin}, ultra vibrant, high contrast, no text"
            if bias == "BULLISH"
            else f"dramatic 3D crypto market illustration of red lightning hitting a glass chart floor with a giant red arrow pointing down for {base_coin}, cinematic dark lighting, no text"
        )
        payload = json.dumps({"prompt": scene, "num_steps": 4}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            img_bytes = resp.read()
            if len(img_bytes) > 1000:
                out_file = Path(output_path)
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_bytes(img_bytes)
                return str(out_file.resolve())
    except Exception:
        pass
    return None


def get_cloudflare_credentials() -> Tuple[str, str]:
    acc_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    return acc_id, token


def generate_text_cloudflare(system_prompt: str, user_prompt: str) -> Optional[str]:
    acc_id, token = get_cloudflare_credentials()
    if not (acc_id and token):
        return None
    for model_name in (CF_TEXT_MODEL, CF_TEXT_FALLBACK_MODEL):
        try:
            url = clean_url(f"{CF_API_HOST}/client/v4/accounts/{acc_id}/ai/run/{model_name}")
            payload = json.dumps({
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 160,
                "temperature": 0.85,
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = ((data.get("result") or {}).get("response") or "").strip()
                if 45 < len(text) < 700:
                    return sanitize_human_post_text(text)
        except Exception:
            continue
    return None


def generate_matrix_fallback_text(
    market_data: Dict[str, object],
    persona: Dict[str, str],
    visual_format: str,
) -> str:
    """জিরো-টেমপ্লেট ফলব্যাক: কোনো ফিক্সড স্ট্যাটিক লাইন ছাড়াই ডায়নামিকালি মানবীয় বাক্য জোড়া লাগায়"""
    tag = market_data["cashtag"]
    p = format_price(float(market_data["last_price"]))
    sup = format_price(float(market_data["support"]))
    res = format_price(float(market_data["resistance"]))
    ema = format_price(float(market_data["ema20"]))
    chg = float(market_data["change_24h"])
    vol = f"${float(market_data['quote_vol_24h'])/1e6:,.1f}M"
    is_bull = market_data["bias"] == "BULLISH"

    if visual_format == "TRADER_POLL":
        intros = [
            f"{tag} is battling right at the {ema} pivot with {vol} in 24h turnover.",
            f"Massive volume cluster forming on {tag} around {p}.",
            f"Orderflow on {tag} is getting crowded near the {res if is_bull else sup} level.",
        ]
        poll_q = (
            f"Where does {tag} close today?\n"
            f"[A] Break above {res} cleanly\n"
            f"[B] Flush down to {sup} liquidity\n"
            f"[C] Choppy sideways bleed"
        )
        return f"{random.choice(intros)}\n\n{poll_q}"

    if visual_format == "CHEAT_SHEET_ALPHA":
        return (
            f"1H TRADING RADAR: {tag} ({chg:+.2f}%)\n\n"
            f"▸ Current Tape: {p}\n"
            f"▸ Buyer Floor: {sup}\n"
            f"▸ Seller Ceiling: {res}\n"
            f"▸ Invalidation: Hourly close past {ema}\n\n"
            f"Are you leaning long or waiting for the flush? Drop thoughts 👇"
        )

    # সাধারণ অ্যানালাইসিসের জন্য ন্যাচারাল সেন্টেন্স কম্বিনেশন
    if is_bull:
        hooks = [
            f"Clean absorption on {tag} after defending the {sup} demand base ({chg:+.2f}%).",
            f"Spot buyers stepped in aggressively on {tag} at {p}, soaking up the dip with {vol} volume.",
            f"{tag} just held {sup} with strength while sellers failed to push lower.",
        ]
        middles = [
            f"As long as 1H candles close above {ema}, the path of least resistance points toward {res}.",
            f"Holding above {ema} keeps the momentum intact for a test of the {res} liquidity wall.",
            f"If buyers maintain control over the {ema} zone, expect a breakout continuation toward {res}.",
        ]
        closes_q = [
            f"Taking the {tag} breakout or waiting for a pullback? 👇",
            f"Who is eyeing {res} before the session close? 👇",
            f"Are bulls ready to blast through {res}? 👇",
        ]
    else:
        hooks = [
            f"Heavy seller exhaustion showing on {tag} around {p} ({chg:+.2f}%).",
            f"Weak bounce attempts on {tag} are getting absorbed right below the {ema} level.",
            f"Bears rejected {tag} near {res} on ${vol} turnover, shifting 1H structure downward.",
        ]
        middles = [
            f"Until bulls reclaim {ema} on convincing volume, momentum targets the {sup} floor.",
            f"Sustained rejection under {ema} leaves the door open for a stop-hunt into {sup}.",
            f"Sellers are capping every minor push, favoring a liquidity sweep toward {sup}.",
        ]
        closes_q = [
            f"Shorting down to {sup} or waiting for the sweep? 👇",
            f"Does {sup} hold on {tag} or do we flush lower? 👇",
            f"Playing the breakdown or staying patient on the sidelines? 👇",
        ]

    return f"{random.choice(hooks)}\n\n{random.choice(middles)}\n\n{random.choice(closes_q)}"


def build_human_post_by_persona(
    market_data: Dict[str, object],
    session_info: Dict[str, object],
    persona: Dict[str, str],
    visual_format: str,
) -> str:
    primary_tag = str(market_data["cashtag"])
    base_coin = str(market_data["base_coin"])
    companion_pool = [t for t in ["$BTC", "$ETH", "$SOL", "$BNB"] if t != primary_tag]
    secondary_tags = random.sample(companion_pool, 2)
    cashtag_footer = f"{primary_tag} {secondary_tags[0]} {secondary_tags[1]}"
    tag_line = f"{cashtag_footer} #{base_coin} #Write2Earn #BinanceSquare"

    price_str = format_price(float(market_data["last_price"]))
    sup_str = format_price(float(market_data["support"]))
    res_str = format_price(float(market_data["resistance"]))
    target_str = format_price(float(market_data["target_price"]))
    ema20_str = format_price(float(market_data["ema20"]))
    chg = float(market_data["change_24h"])
    vol_m = float(market_data["quote_vol_24h"]) / 1e6
    bias = str(market_data["bias"])

    # এআই প্রম্পট - কন্টেন্ট ফরম্যাট অনুযায়ী সম্পূর্ণ গতিশীল
    if visual_format == "TRADER_POLL":
        system_prompt = (
            "You are an active crypto trader on Binance Square. "
            "Write a brief 1-sentence observation on price action, followed by a 3-choice community poll. "
            "STRICT RULES: Do not use Markdown (**), no greetings, no hashtags. Under 40 words total."
        )
        user_prompt = (
            f"Coin: {primary_tag} at {price_str} ({chg:+.2f}%). Support: {sup_str}, Resistance: {res_str}. "
            "Output format:\n[1 sentence on orderflow]\n[Question]\n[A] ...\n[B] ...\n[C] ..."
        )
    elif visual_format == "CHEAT_SHEET_ALPHA":
        system_prompt = (
            "You are a disciplined floor trader. Write a clean, 4-bullet trade radar snapshot. "
            "STRICT RULES: Use '▸ ' for bullets. No bold (**), no greetings, no hashtags. Under 50 words total."
        )
        user_prompt = (
            f"Coin: {primary_tag} at {price_str}. Key levels: Sup {sup_str}, Res {res_str}, EMA20 {ema20_str}. Bias: {bias}. "
            "Format:\n1H RADAR: [Coin]\n▸ Level 1\n▸ Level 2\n▸ Level 3\n▸ Question for traders"
        )
    else:
        system_prompt = (
            f"You are a professional crypto orderflow trader on Binance Square ({persona['name']}). "
            f"Persona strategy: {persona['angle']}. "
            "Write a punchy, ultra-realistic 3-sentence trading note (strictly 45 to 70 words). "
            "STRICT RULES: "
            "1. NEVER use 'Hey guys', 'In conclusion', 'Furthermore', or intro fluff. "
            "2. NEVER mention 'chart arrows' or colors. Talk strictly about price levels, wicks, and invalidation. "
            "3. NO Markdown bold asterisks (**). End with a short engaging question. NO hashtags."
        )
        user_prompt = (
            f"Coin: {primary_tag} at {price_str} ({chg:+.2f}%, Vol ${vol_m:,.1f}M).\n"
            f"Key Levels: Support {sup_str}, Resistance {res_str}, 1H EMA20 {ema20_str}. Bias: {bias} toward {target_str}.\n"
            "Write the human trader note now:"
        )

    cf_body = generate_text_cloudflare(system_prompt, user_prompt)
    if cf_body and primary_tag in cf_body:
        cf_body = re.sub(r"(?:\s*#[A-Za-z0-9_]+)+\s*$", "", cf_body).strip()
        return sanitize_human_post_text(f"{cf_body}\n\n{tag_line}")

    # ফলব্যাক ম্যাট্রিক্স থেকে স্বয়ংক্রিয় বৈচিত্র্যময় টেক্সট
    fallback_body = generate_matrix_fallback_text(market_data, persona, visual_format)
    return sanitize_human_post_text(f"{fallback_body}\n\n{tag_line}")


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
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path))
        candidates.append(Path(custom_path) / "scripts")
    candidates.extend([
        Path("square-post"),
        Path("square-post/scripts"),
        Path.cwd() / "square-post/scripts",
    ])
    for c in candidates:
        if (c / "post-image.mjs").exists():
            return c
        if (c / "scripts/post-image.mjs").exists():
            return c / "scripts"
    return None


def broadcast_to_telegram(
    post_text: str,
    image_path: Optional[str] = None,
    square_post_url: Optional[str] = None,
) -> bool:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not (bot_token and chat_id):
        return False

    link_suffix = ""
    if square_post_url and "unavailable" not in str(square_post_url):
        link_suffix = f"\n\n🔗 Trade & View on Binance Square:\n{square_post_url}"

    full_message = f"{post_text}{link_suffix}"

    try:
        if image_path and Path(image_path).exists():
            photo_url = clean_url(f"{TG_API_HOST}/bot{bot_token}/sendPhoto")
            caption_text = full_message[:1020]
            with open(image_path, "rb") as photo_file:
                boundary = "----WebKitFormBoundary" + hex(int(time.time() * 1000))[2:]
                body = bytearray()
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode("utf-8"))
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption_text}\r\n'.encode("utf-8"))
                filename = Path(image_path).name
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode("utf-8"))
                body.extend(b"Content-Type: image/png\r\n\r\n")
                body.extend(photo_file.read())
                body.extend(b"\r\n")
                body.extend(f"--{boundary}--\r\n".encode("utf-8"))

                req = urllib.request.Request(
                    photo_url, data=bytes(body),
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    return bool(res.get("ok"))

        msg_url = clean_url(f"{TG_API_HOST}/bot{bot_token}/sendMessage")
        payload = json.dumps({"chat_id": chat_id, "text": full_message[:4090]}).encode("utf-8")
        req = urllib.request.Request(msg_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok"))
    except Exception as exc:
        print(f"[WARN] Telegram sync skipped: {exc}")
        return False


def broadcast_to_webhook(
    post_text: str,
    image_url: Optional[str] = None,
    square_post_url: Optional[str] = None,
    coin: Optional[str] = None,
) -> bool:
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("[WARN] MAKE_WEBHOOK_URL missing, skipping webhook broadcast.")
        return False

    link_url = (
        square_post_url
        if (square_post_url and "unavailable" not in str(square_post_url))
        else "[https://www.binance.com/en/square/profile/alphapulse_io](https://www.binance.com/en/square/profile/alphapulse_io)"
    )

    payload = {
        "text": post_text.strip(),
        "image_url": image_url or "",
        "square_url": link_url,
        "coin": coin or "CRYPTO",
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status in (200, 201, 204):
                print("[+] Successfully sent data to Make.com Webhook!")
                return True
        print(f"[WARN] Webhook send status: {resp.status}")
    except Exception as exc:
        print(f"[WARN] Webhook request error: {exc}")
    return False


def publish_to_binance_square(
    post_text: str,
    image_paths: List[str],
    square_skill_dir: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, object]:
    if dry_run:
        return {
            "status": "DRY_RUN_SUCCESS",
            "post_url": clean_url(f"{SQUARE_POST_BASE_URL}DRY_RUN_PREVIEW"),
            "images": image_paths,
        }

    api_key = os.environ.get("BINANCE_SQUARE_OPENAPI_KEY", "").strip()
    if not api_key:
        key_file = Path.home() / ".config" / "binance-square" / "openapi-key"
        if key_file.exists():
            api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError("Missing BINANCE_SQUARE_OPENAPI_KEY!")

    scripts_dir = find_square_skill_scripts_dir(square_skill_dir)
    if scripts_dir:
        env = {**os.environ, "BINANCE_SQUARE_OPENAPI_KEY": api_key}
        resolved_images = [str(Path(p).resolve()) for p in image_paths if Path(p).exists()]

        if resolved_images:
            script_file = scripts_dir / "post-image.mjs"
            cmd = ["node", str(script_file), "--text", post_text, "--images", ",".join(resolved_images)]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                return {"status": "PUBLISHED_WITH_IMAGES", "stdout": proc.stdout.strip(), "images": resolved_images}
            print(f"[WARN] post-image.mjs non-zero ({proc.stderr}), falling back.")
        else:
            script_file = scripts_dir / "post-text.mjs"
            cmd = ["node", str(script_file), "--text", post_text]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=40)
            if proc.returncode == 0:
                return {"status": "PUBLISHED_PURE_TEXT", "stdout": proc.stdout.strip(), "images": []}

    payload = json.dumps({"bodyTextOnly": post_text}).encode("utf-8")
    req = urllib.request.Request(
        clean_url(BINANCE_SQUARE_OPENAPI_URL),
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
            "post_url": clean_url(f"{SQUARE_POST_BASE_URL}{content_id}"),
            "images": image_paths,
        }
    raise RuntimeError(f"Binance Square API Error ({code}): {result}")


def run_single_cycle(
    output_dir: str,
    memory_file: str = "./bot_memory.json",
    force_format: Optional[str] = None,
    square_skill_dir: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, object]:
    session_info = get_current_global_session()
    memory = load_bot_memory(memory_file)

    if force_format:
        visual_format = force_format
    else:
        avail_formats = [f for f in VISUAL_FORMATS if f not in memory["recent_formats"][-2:]]
        visual_format = random.choice(avail_formats or VISUAL_FORMATS)

    avail_personas = [p for p in HUMAN_PERSONAS if p["id"] not in memory["recent_personas"]]
    persona = random.choice(avail_personas or HUMAN_PERSONAS)

    market_data = scan_trending_market_candidate(memory["recent_coins"])
    base_coin = str(market_data["base_coin"])

    post_text = build_human_post_by_persona(market_data, session_info, persona, visual_format)

    image_list: List[str] = []
    if visual_format == "MOBILE_ARROW_CHART":
        fname = build_seo_image_filename(base_coin, visual_format, "mobile-perp")
        img_path = generate_mobile_arrow_chart(market_data, str(Path(output_dir) / fname))
        image_list.append(img_path)

    elif visual_format == "PRO_SETUP_BOX_CHART":
        fname = build_seo_image_filename(base_coin, visual_format, "1h-rr-setup")
        img_path = generate_pro_setup_box_chart(market_data, session_info, str(Path(output_dir) / fname))
        image_list.append(img_path)

    elif visual_format == "VOLATILITY_SHOCK_CARD":
        fname = build_seo_image_filename(base_coin, visual_format, "volatility-card")
        img_path = generate_volatility_shock_card(market_data, str(Path(output_dir) / fname))
        image_list.append(img_path)

    elif visual_format == "DUAL_COMBO_POST":
        fname1 = build_seo_image_filename(base_coin, visual_format, "mobile-chart")
        img1 = generate_mobile_arrow_chart(market_data, str(Path(output_dir) / fname1))
        image_list.append(img1)
        fname2 = build_seo_image_filename(base_coin, visual_format, "market-mood")
        img2 = generate_cloudflare_reaction_visual(base_coin, str(market_data["bias"]), str(Path(output_dir) / fname2))
        if img2:
            image_list.append(img2)
    # TRADER_POLL ও CHEAT_SHEET_ALPHA ফরম্যাটে ক্লিন টেক্সট অগ্রাধিকার পায়

    pub_result = publish_to_binance_square(
        post_text=post_text,
        image_paths=image_list,
        square_skill_dir=square_skill_dir,
        dry_run=dry_run,
    )

    first_image = image_list[0] if image_list else None
    tg_status = broadcast_to_telegram(
        post_text=post_text,
        image_path=first_image,
        square_post_url=pub_result.get("post_url"),
    )

    extracted_image_url = None
    extracted_post_url = pub_result.get("post_url") or pub_result.get("link") or pub_result.get("url")
    if isinstance(pub_result, dict):
        stdout_content = pub_result.get("stdout", "")
        for line in stdout_content.splitlines():
            if "Ready:" in line and "http" in line and not extracted_image_url:
                extracted_image_url = line.split("Ready:", 1)[1].strip()
            if "binance.com" in line and "/square/post/" in line:
                m_url = re.search(r"(https?://[^\s\"'>]+)", line)
                if m_url:
                    extracted_post_url = m_url.group(1).strip()

    x_status = broadcast_to_webhook(
        post_text=post_text,
        image_url=extracted_image_url,
        square_post_url=extracted_post_url,
        coin=base_coin,
    )

    save_bot_memory(memory_file, memory, base_coin, persona["id"], visual_format)

    return {
        "format": visual_format,
        "persona": persona["id"],
        "session": session_info["name"],
        "symbol": market_data["symbol"],
        "cashtag": market_data["cashtag"],
        "bias": market_data["bias"],
        "images": image_list,
        "post_text": post_text,
        "publish_result": pub_result,
        "telegram_synced": tg_status,
        "webhook_synced": x_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Binance Square V4.0 Viral Human Auto-Bot")
    parser.add_argument("--once", action="store_true", help="Run a single post cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Preview locally without publishing.")
    parser.add_argument(
        "--format",
        choices=[
            "MOBILE_ARROW_CHART", "PRO_SETUP_BOX_CHART",
            "VOLATILITY_SHOCK_CARD", "TRADER_POLL", "CHEAT_SHEET_ALPHA", "DUAL_COMBO_POST",
        ],
        help="Force a specific visual format.",
    )
    parser.add_argument("--output-dir", default="./generated_charts", help="Directory for chart PNGs.")
    parser.add_argument("--memory-file", default="./bot_memory.json", help="Path to anti-repetition state file.")
    parser.add_argument("--square-skill-dir", default=os.environ.get("SQUARE_SKILL_DIR", ""), help="Path to square-post skill.")
    args = parser.parse_args()

    if args.once:
        summary = run_single_cycle(
            output_dir=args.output_dir,
            memory_file=args.memory_file,
            force_format=args.format,
            square_skill_dir=args.square_skill_dir or None,
            dry_run=args.dry_run,
        )
        print("=" * 78)
        print(f"[FORMAT]    {summary['format']}  |  [PERSONA] {summary['persona']}")
        print(f"[COIN]      {summary['symbol']} ({summary['cashtag']})  |  [BIAS] {summary['bias']}")
        print(f"[SESSION]   {summary['session']}")
        print(f"[FILES]     {summary['images']}")
        print("-" * 78)
        print(summary["post_text"])
        print("-" * 78)
        print(f"[STATUS]    {summary['publish_result']}")
        print(f"[TELEGRAM]  Synced: {summary['telegram_synced']}")
        print(f"[WEBHOOK]   Synced: {summary['webhook_synced']}")
        print("=" * 78)
        return

    print("[START] Launching V4.0 Peak-Session Engagement Scheduler...")
    while True:
        try:
            summary = run_single_cycle(
                output_dir=args.output_dir,
                memory_file=args.memory_file,
                square_skill_dir=args.square_skill_dir or None,
                dry_run=args.dry_run,
            )
            print(
                f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M UTC')}] "
                f"{summary['cashtag']} [{summary['format']} / {summary['persona']}] -> {summary['publish_result']['status']}"
            )
        except Exception as exc:
            print(f"[ERROR] Cycle failed: {exc}")

        session = get_current_global_session()
        base_wait = int(session["interval_minutes"]) * 60
        jitter_seconds = random.randint(-600, 600)  # ±10 মিনিট অ্যান্টি-বট জ্যামিং
        sleep_seconds = max(5400, base_wait + jitter_seconds)  # কমপক্ষে ১.৫ থেকে ৩.৫ ঘণ্টা ব্যবধান
        print(f"[SCHEDULER] {session['name']} | Next post in {sleep_seconds // 60}m...")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
