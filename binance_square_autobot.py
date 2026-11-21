#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BINANCE SQUARE WRITE-TO-EARN AUTO-BOT V5.0
(LIVE NEWS + 40-30-20-10 NARRATIVE ENGINE + MULTI-TIMEFRAME + ZERO CASHTAG SPAM)
File Name: binance_square_autobot.py
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import random
import re
import subprocess
import textwrap
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

CF_TEXT_MODEL = os.environ.get("CF_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8")
CF_TEXT_FALLBACK_MODEL = "@cf/mistral/mistral-7b-instruct-v0.2-lora"

CRYPTO_RSS_FEEDS = [
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("CryptoSlate", "https://cryptoslate.com/feed/"),
]

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

NEWS_COIN_KEYWORDS = {
    "bitcoin": "BTC", "btc": "BTC", "satoshi": "BTC",
    "ethereum": "ETH", "eth": "ETH", "vitalik": "ETH", "ether": "ETH",
    "solana": "SOL", "sol": "SOL",
    "binance": "BNB", "bnb": "BNB",
    "ripple": "XRP", "xrp": "XRP",
    "dogecoin": "DOGE", "doge": "DOGE",
    "cardano": "ADA", "ada": "ADA",
    "sui": "SUI", "avalanche": "AVAX", "avax": "AVAX",
    "chainlink": "LINK", "link": "LINK",
    "pepe": "PEPE", "shiba": "SHIB", "shib": "SHIB",
    "toncoin": "TON", "ton": "TON",
    "arbitrum": "ARB", "optimism": "OP",
    "aave": "AAVE", "uniswap": "UNI", "near": "NEAR",
    "bittensor": "TAO", "render": "RENDER", "ondo": "ONDO",
    "ethena": "ENA", "litecoin": "LTC", "polkadot": "DOT",
    "aptos": "APT", "injective": "INJ", "celestia": "TIA",
}

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

# 40-30-20-10 Weighted Content Mix
PILLAR_WEIGHTS = [
    ("BREAKING_NEWS_TAKE", 40),
    ("HIGH_CONVICTION_CHART", 30),
    ("TRADING_PSYCHOLOGY", 20),
    ("COMMUNITY_DEBATE", 10),
]

PSYCHOLOGY_TOPICS = [
    ("Why 90% of traders get liquidated on the first breakout candle", "Fakeout breakouts trap high-leverage retail longs before the real move starts."),
    ("Moving your stop-loss further away is not patience — it is hope", "Widening invalidation levels turns small manageable cuts into account-blowing losses."),
    ("Over-trading in sideways chop destroys more accounts than crashes", "Sitting in cash during low-volume ranges is an active winning position."),
    ("Why copying 20x leverage screenshots is the fastest way to zero", "Survivorship bias hides the 15 liquidated entries behind one green PnL card."),
    ("The hidden trap of positive funding rates during slow grinds up", "When everyone is paying high funding to stay long, a 3% wick wipes out late entries."),
    ("Taking partial profits early beats round-tripping a 40% unrealized gain", "Unrealized green numbers vanish in one hourly candle without a scaling-out plan."),
    ("Stop chasing green candles after a +12% daily pump", "Buying vertical extensions makes you exit liquidity for early spot buyers."),
    ("Why trading 1-minute charts ruins your bias on the 4H trend", "Zooming in creates emotional noise and forces premature exits on healthy pullbacks."),
    ("Risking 2% per trade sounds boring until you hit a 5-loss streak", "Position sizing is the only edge that keeps you alive long enough to catch a trend."),
    ("Never revenge trade right after getting stopped out", "An emotional re-entry doubles size on lower-quality setups and compounds drawdowns."),
]

GLOBAL_SESSIONS = {
    "ASIA_PEAK": {"name": "Asian Session", "utc_hours": (0, 8)},
    "EUROPE_LONDON_PEAK": {"name": "London Session", "utc_hours": (8, 13)},
    "US_EUROPE_OVERLAP_PEAK": {"name": "US & London Overlap", "utc_hours": (13, 21)},
    "LATE_US_PACIFIC": {"name": "Daily Close Session", "utc_hours": (21, 24)},
}


def load_bot_memory(memory_file: str) -> Dict[str, List[str]]:
    path = Path(memory_file)
    default_mem = {
        "recent_coins": [],
        "recent_pillars": [],
        "recent_news_hashes": [],
        "recent_psych_topics": [],
        "recent_chart_styles": [],
    }
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "recent_coins": list(data.get("recent_coins", []))[-12:],
                "recent_pillars": list(data.get("recent_pillars", []))[-6:],
                "recent_news_hashes": list(data.get("recent_news_hashes", []))[-40:],
                "recent_psych_topics": list(data.get("recent_psych_topics", []))[-8:],
                "recent_chart_styles": list(data.get("recent_chart_styles", []))[-4:],
            }
        except Exception:
            pass
    return default_mem


def save_bot_memory(
    memory_file: str,
    memory: Dict[str, List[str]],
    coin: str,
    pillar: str,
    news_hash: Optional[str] = None,
    psych_topic: Optional[str] = None,
    chart_style: Optional[str] = None,
) -> None:
    memory["recent_coins"] = (memory.get("recent_coins", []) + [coin])[-12:]
    memory["recent_pillars"] = (memory.get("recent_pillars", []) + [pillar])[-6:]
    if news_hash:
        memory["recent_news_hashes"] = (memory.get("recent_news_hashes", []) + [news_hash])[-40:]
    if psych_topic:
        memory["recent_psych_topics"] = (memory.get("recent_psych_topics", []) + [psych_topic])[-8:]
    if chart_style:
        memory["recent_chart_styles"] = (memory.get("recent_chart_styles", []) + [chart_style])[-4:]
    path = Path(memory_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def choose_next_pillar(recent_pillars: List[str], force_format: Optional[str] = None) -> str:
    if force_format:
        mapping = {
            "BREAKING_NEWS_TAKE": "BREAKING_NEWS_TAKE",
            "HIGH_CONVICTION_CHART": "HIGH_CONVICTION_CHART",
            "TRADING_PSYCHOLOGY": "TRADING_PSYCHOLOGY",
            "COMMUNITY_DEBATE": "COMMUNITY_DEBATE",
            "MOBILE_ARROW_CHART": "HIGH_CONVICTION_CHART",
            "PRO_SETUP_BOX_CHART": "HIGH_CONVICTION_CHART",
            "VOLATILITY_SHOCK_CARD": "HIGH_CONVICTION_CHART",
            "TRADER_POLL": "COMMUNITY_DEBATE",
            "CHEAT_SHEET_ALPHA": "HIGH_CONVICTION_CHART",
        }
        if force_format in mapping:
            return mapping[force_format]

    last_pillar = recent_pillars[-1] if recent_pillars else None
    candidates = [(p, w) for p, w in PILLAR_WEIGHTS if p != last_pillar]
    pillars = [c[0] for c in candidates]
    weights = [c[1] for c in candidates]
    return random.choices(pillars, weights=weights, k=1)[0]


def sanitize_human_post_text(raw_text: str) -> str:
    text = raw_text.strip()
    for label in (
        "BREAKING_NEWS_TAKE", "HIGH_CONVICTION_CHART", "TRADING_PSYCHOLOGY",
        "COMMUNITY_DEBATE", "Headline:", "Post:", "Analysis:", "Hot Take:",
    ):
        text = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(
        r"^(?:Hey|Hi|Hello|Yo|What's up|Greetings)\s+"
        r"(?:guys|friends|traders|everyone|squad|fam|team|folks|crypto fam)"
        r"(?:\s+on\s+Binance\s+Square)?[\s,!.\-—👋👀🔥]*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\b(?:Furthermore|Moreover|In conclusion|To summarize|As we can see|It is worth noting|In summary|Delving into),?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b[Tt]he\s+(?:red|green)\s+(?:chart\s+)?arrow\b", "price structure", text)
    text = re.sub(r"(\$[A-Z0-9]{2,10})\s+([,.:;!?])", r"\1\2", text)
    text = re.sub(r"(\$[A-Z0-9]{2,10})\s*/\s*USDT", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("```", "").replace('"', "")
    text = re.sub(r"(?m)^#{1,4}\s*", "", text)
    text = re.sub(r"(?m)^\s*[\*\-]\s+", "▸ ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_seo_image_filename(base_coin: str, pillar: str, suffix: str = "visual") -> str:
    coin_slug = COIN_SEO_SLUGS.get(base_coin.upper(), base_coin.lower())
    date_slug = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H%M")
    return f"{coin_slug}-{pillar.lower().replace('_', '-')}-{suffix}-{date_slug}.png"


def http_get_raw(url: str, timeout: int = 12) -> Optional[str]:
    try:
        safe_u = clean_url(url)
        req = urllib.request.Request(
            safe_u,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/rss+xml, application/xml, application/json, text/xml, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def http_get_json(url: str, timeout: int = 12) -> Optional[object]:
    raw = http_get_raw(url, timeout=timeout)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def fetch_binance_spot_json(path: str) -> Optional[object]:
    for base in BINANCE_SPOT_ENDPOINTS:
        res = http_get_json(f"{base}{path}")
        if res is not None:
            return res
    return None


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


def detect_coin_from_text(text: str) -> str:
    lower_t = text.lower()
    for kw, ticker in NEWS_COIN_KEYWORDS.items():
        if re.search(rf"\b{re.escape(kw)}\b", lower_t):
            return ticker
    return "BTC"


def fetch_live_crypto_news(recent_hashes: List[str]) -> Optional[Dict[str, str]]:
    """রিয়েল-টাইম RSS ফিড থেকে একদম নতুন ক্রিপ্টো নিউজ সংগ্রহ করে।"""
    feeds = list(CRYPTO_RSS_FEEDS)
    random.shuffle(feeds)
    collected: List[Dict[str, str]] = []

    for source_name, feed_url in feeds:
        xml_data = http_get_raw(feed_url, timeout=12)
        if not xml_data:
            continue
        try:
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")[:8]
            for item in items:
                title_el = item.find("title")
                desc_el = item.find("description")
                if title_el is None or not title_el.text:
                    continue
                title = html.unescape(title_el.text).strip()
                desc_raw = html.unescape(desc_el.text).strip() if (desc_el is not None and desc_el.text) else ""
                desc_clean = re.sub(r"<[^>]+>", " ", desc_raw)
                desc_clean = re.sub(r"\s+", " ", desc_clean).strip()[:320]

                if any(bad in title.lower() for bad in ("sponsored", "press release", "price prediction", "best presale", "casino")):
                    continue

                title_hash = hashlib.md5(title.lower().encode("utf-8")).hexdigest()[:12]
                if title_hash in recent_hashes:
                    continue

                detected_coin = detect_coin_from_text(f"{title} {desc_clean}")
                collected.append({
                    "source": source_name,
                    "title": title,
                    "summary": desc_clean,
                    "coin": detected_coin,
                    "hash": title_hash,
                })
        except Exception:
            continue

    if not collected:
        return None
    return random.choice(collected[:6])


def fetch_single_coin_snapshot(base_coin: str) -> Dict[str, object]:
    symbol = f"{base_coin.upper()}USDT"
    ticker = fetch_binance_spot_json(f"/api/v3/ticker/24hr?symbol={symbol}")
    if isinstance(ticker, dict) and "lastPrice" in ticker:
        return {
            "symbol": symbol,
            "base_coin": base_coin.upper(),
            "cashtag": f"${base_coin.upper()}",
            "last_price": float(ticker["lastPrice"]),
            "change_24h": float(ticker.get("priceChangePercent", 0.0)),
            "high_24h": float(ticker.get("highPrice", ticker["lastPrice"])),
            "low_24h": float(ticker.get("lowPrice", ticker["lastPrice"])),
            "quote_vol_24h": float(ticker.get("quoteVolume", 0.0)),
        }
    return {
        "symbol": "BTCUSDT",
        "base_coin": "BTC",
        "cashtag": "$BTC",
        "last_price": 0.0,
        "change_24h": 0.0,
        "high_24h": 0.0,
        "low_24h": 0.0,
        "quote_vol_24h": 0.0,
    }


def is_commission_eligible_symbol(symbol: str, valid_spot_symbols: set) -> bool:
    if not symbol.endswith("USDT") or symbol not in valid_spot_symbols:
        return False
    base = symbol[:-4]
    if base in ZERO_COMMISSION_BLACKLIST or not base.isalpha() or not (2 <= len(base) <= 9):
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


def scan_high_conviction_chart_candidate(
    recent_coins: List[str],
    timeframe: str = "4h",
) -> Dict[str, object]:
    """শুধুমাত্র আসল ভলিউম ও উল্লেখযোগ্য মুভমেন্ট থাকা কয়েন নির্বাচন করে।"""
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
            if sym.endswith("USDT") and vol >= 25_000_000:
                valid_spot_map[sym] = t

    valid_spot_symbols = set(valid_spot_map.keys())
    eligible_pool: List[dict] = []

    if isinstance(futures_tickers, list) and valid_spot_symbols:
        for ft in futures_tickers:
            sym = str(ft.get("symbol", ""))
            if not is_commission_eligible_symbol(sym, valid_spot_symbols):
                continue
            if float(ft.get("quoteVolume", 0.0)) < 50_000_000:
                continue
            eligible_pool.append(valid_spot_map[sym])

    if not eligible_pool and valid_spot_map:
        eligible_pool = [st for sym, st in valid_spot_map.items() if is_commission_eligible_symbol(sym, valid_spot_symbols)]

    fresh_pool = [t for t in eligible_pool if t["symbol"].replace("USDT", "") not in recent_coins]
    if not fresh_pool:
        fresh_pool = eligible_pool

    high_vol_pool = [t for t in fresh_pool if abs(float(t.get("priceChangePercent", 0.0))) >= 4.0]
    target_pool = high_vol_pool if high_vol_pool else fresh_pool

    selected_symbol = "BTCUSDT"
    ticker_info = None
    if target_pool:
        target_pool.sort(key=lambda x: abs(float(x.get("priceChangePercent", 0.0))), reverse=True)
        major_movers = [t for t in target_pool if t["symbol"] in HIGH_COMMISSION_MAJORS]
        if major_movers and random.random() < 0.55:
            ticker_info = random.choice(major_movers[:5])
        else:
            ticker_info = random.choice(target_pool[:6])
        selected_symbol = ticker_info["symbol"]
    else:
        selected_symbol = random.choice(HIGH_COMMISSION_MAJORS[:8])

    raw_klines = fetch_binance_spot_json(f"/api/v3/klines?symbol={selected_symbol}&interval={timeframe}&limit=48")
    if not isinstance(raw_klines, list) or len(raw_klines) < 25:
        raise RuntimeError(f"Unable to fetch live Binance klines for {selected_symbol} ({timeframe})")

    timestamps = [int(k[0]) for k in raw_klines]
    opens = [float(k[1]) for k in raw_klines]
    highs = [float(k[2]) for k in raw_klines]
    lows = [float(k[3]) for k in raw_klines]
    closes = [float(k[4]) for k in raw_klines]
    volumes = [float(k[5]) for k in raw_klines]
    last_price = closes[-1]

    if ticker_info:
        high_24h = float(ticker_info.get("highPrice", max(highs[-10:])))
        low_24h = float(ticker_info.get("lowPrice", min(lows[-10:])))
        change_24h = float(ticker_info.get("priceChangePercent", 0.0))
        quote_vol_24h = float(ticker_info.get("quoteVolume", 0.0))
    else:
        high_24h = max(highs[-10:])
        low_24h = min(lows[-10:])
        change_24h = ((closes[-1] - closes[-6]) / closes[-6]) * 100.0
        quote_vol_24h = sum(v * c for v, c in zip(volumes[-10:], closes[-10:]))

    ema20 = compute_ema(closes, 20)
    ema50 = compute_ema(closes, 35)
    rsi14 = compute_rsi(closes, 14)

    lookback = min(18, len(lows))
    recent_support = min(lows[-lookback:])
    recent_resistance = max(highs[-lookback:])
    base_coin = selected_symbol.replace("USDT", "")
    funding_pct = funding_map.get(selected_symbol, 0.0085)

    dist_to_res = abs(recent_resistance - last_price)
    dist_to_sup = abs(last_price - recent_support)
    is_bullish_bias = (
        (change_24h >= 2.0 and float(rsi14[-1]) < 72)
        or (float(rsi14[-1]) <= 34)
        or (last_price >= float(ema20[-1]) and dist_to_sup < dist_to_res)
    )
    bias_label = "BULLISH" if is_bullish_bias else "BEARISH"
    target_price = recent_resistance if is_bullish_bias else recent_support

    return {
        "symbol": selected_symbol,
        "base_coin": base_coin,
        "cashtag": f"${base_coin}",
        "timeframe": timeframe.upper(),
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


def generate_news_editorial_card(
    news_item: Dict[str, str],
    coin_snap: Dict[str, object],
    output_path: str,
) -> str:
    """ব্রেকিং নিউজের জন্য ক্লিন এডিটোরিয়াল ডার্ক-মোড ভিজ্যুয়াল কার্ড।"""
    bg_dark = "#0B0E11"
    card_bg = "#141821"
    gold = "#F0B90B"
    bull_green = "#0ECB81"
    bear_red = "#F6465D"
    text_white = "#F3F4F6"
    text_muted = "#848E9C"

    chg = float(coin_snap.get("change_24h", 0.0))
    last_p = float(coin_snap.get("last_price", 0.0))
    accent = bull_green if chg >= 0 else bear_red

    fig = plt.figure(figsize=(10, 6.2), dpi=150, facecolor=bg_dark)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=bg_dark)
    ax.axis("off")

    card = mpatches.FancyBboxPatch(
        (0.04, 0.06), 0.92, 0.88,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor=card_bg, edgecolor="#2B3139", linewidth=1.8,
    )
    ax.add_patch(card)

    bar = mpatches.FancyBboxPatch(
        (0.07, 0.82), 0.25, 0.065,
        boxstyle="round,pad=0.008,rounding_size=0.015",
        facecolor=gold, edgecolor="none",
    )
    ax.add_patch(bar)
    ax.text(0.195, 0.852, "MARKET CATALYST", color="#0B0E11", fontsize=11, fontweight="bold", ha="center", va="center")
    ax.text(0.93, 0.852, f"SOURCE: {news_item['source'].upper()}", color=text_muted, fontsize=10, fontweight="bold", ha="right", va="center")

    wrapped_title = textwrap.fill(news_item["title"], width=38)
    ax.text(0.07, 0.72, wrapped_title, color=text_white, fontsize=22, fontweight="bold", va="top", linespacing=1.35)

    if last_p > 0:
        strip = mpatches.FancyBboxPatch(
            (0.07, 0.13), 0.86, 0.16,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor="#0B0E11", edgecolor=accent, linewidth=1.4,
        )
        ax.add_patch(strip)
        ax.text(0.10, 0.21, f"LIVE IMPACT:  {coin_snap['cashtag']} / USDT", color=text_muted, fontsize=11, fontweight="bold", va="center")
        ax.text(0.90, 0.21, f"{format_price(last_p)}   ({chg:+.2f}% 24h)", color=accent, fontsize=16, fontweight="bold", ha="right", va="center")

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
    tf = str(market_data.get("timeframe", "4H"))

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
        f"{market_data['base_coin']}USDT  •  {tf} STRUCTURE  •  {session_info['name'].upper()}",
        color=text_primary, fontsize=15, fontweight="bold",
    )
    fig.text(
        0.05, 0.88,
        f"Spot: {format_price(last_p)} ({chg:+.2f}%)   |   Demand: {format_price(sup)}   |   "
        f"Supply: {format_price(res)}   |   {tf} RSI: {float(market_data['rsi']):.1f}",
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

    ax_price.plot(x, ema20, color="#F0B90B", linewidth=1.5, zorder=4)
    ax_price.axhline(sup, color=bull_green, linestyle="--", linewidth=1.0, alpha=0.65)
    ax_price.axhline(res, color=bear_red, linestyle="--", linewidth=1.0, alpha=0.65)

    box_start = n - 2
    box_width = 6.5
    if is_bull:
        tp_level = res
        sl_level = sup * 0.988
        profit_box = mpatches.Rectangle(
            (box_start, last_p), box_width, max(tp_level - last_p, last_p * 0.01),
            facecolor=bull_green, edgecolor=bull_green, alpha=0.22, zorder=5,
        )
        stop_box = mpatches.Rectangle(
            (box_start, sl_level), box_width, max(last_p - sl_level, last_p * 0.005),
            facecolor=bear_red, edgecolor=bear_red, alpha=0.22, zorder=5,
        )
    else:
        tp_level = sup
        sl_level = res * 1.012
        profit_box = mpatches.Rectangle(
            (box_start, tp_level), box_width, max(last_p - tp_level, last_p * 0.01),
            facecolor=bull_green, edgecolor=bull_green, alpha=0.22, zorder=5,
        )
        stop_box = mpatches.Rectangle(
            (box_start, last_p), box_width, max(sl_level - last_p, last_p * 0.005),
            facecolor=bear_red, edgecolor=bear_red, alpha=0.22, zorder=5,
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
    tf = str(market_data.get("timeframe", "4H"))

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
    gs = GridSpec(2, 1, height_ratios=[4.2, 1.0], hspace=0.06, left=0.06, right=0.88, top=0.77, bottom=0.07)

    ax_price = fig.add_subplot(gs[0], facecolor=panel_bg)
    ax_vol = fig.add_subplot(gs[1], facecolor=panel_bg, sharex=ax_price)

    chg = float(market_data["change_24h"])
    chg_sign = "+" if chg >= 0 else ""
    price_col = bull_green if chg >= 0 else bear_red
    last_p = float(market_data["last_price"])

    fig.text(0.06, 0.93, f"{market_data['base_coin']}USDT", color=text_primary, fontsize=22, fontweight="bold")
    fig.text(0.36, 0.935, f"{tf} Chart", color="#F0B90B", fontsize=12, fontweight="bold")
    fig.text(0.06, 0.86, format_price(last_p).replace("$", ""), color=price_col, fontsize=26, fontweight="bold")
    fig.text(0.06, 0.815, f"≈ {format_price(last_p)}   {chg_sign}{chg:.2f}%", color=price_col, fontsize=13, fontweight="bold")

    fig.text(0.58, 0.91, "24h High", color=text_muted, fontsize=10)
    fig.text(0.88, 0.91, format_price(float(market_data["high_24h"])).replace("$", ""), color=text_primary, fontsize=10, ha="right")
    fig.text(0.58, 0.87, "24h Low", color=text_muted, fontsize=10)
    fig.text(0.88, 0.87, format_price(float(market_data["low_24h"])).replace("$", ""), color=text_primary, fontsize=10, ha="right")
    fig.text(0.58, 0.83, "24h Vol", color=text_muted, fontsize=10)
    fig.text(0.88, 0.83, f"${float(market_data['quote_vol_24h'])/1e6:,.1f}M", color=text_primary, fontsize=10, ha="right")

    candle_width = 0.62
    for idx in range(n):
        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        color = bull_green if c >= o else bear_red
        ax_price.plot([idx, idx], [l, h], color=color, linewidth=1.3, zorder=2)
        rect = mpatches.Rectangle(
            (idx - candle_width / 2.0, min(o, c)),
            candle_width,
            max(abs(c - o), (h - l) * 0.04),
            facecolor=color, edgecolor=color, zorder=3,
        )
        ax_price.add_patch(rect)

    ax_price.plot(x, ema20, color=ma7_color, linewidth=1.6, zorder=4)
    ax_price.plot(x, ema50, color=ma25_color, linewidth=1.6, zorder=4)

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

    label_txt = f"KEY ZONE: {format_price(resistance if is_bull else support)}"
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


def generate_text_cloudflare(system_prompt: str, user_prompt: str, max_tokens: int = 280) -> Optional[str]:
    acc_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
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
                "max_tokens": max_tokens,
                "temperature": 0.85,
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=22) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = ((data.get("result") or {}).get("response") or "").strip()
                if 60 < len(text) < 1200:
                    return sanitize_human_post_text(text)
        except Exception:
            continue
    return None


def build_clean_footer(base_coin: str) -> str:
    """কোনো ক্যাশট্যাগ স্প্যামিং ছাড়া ন্যাচারাল ফুটার (শুধু প্রাসঙ্গিক ১টি ট্যাগ)।"""
    if random.random() < 0.25:
        return f"#{base_coin} #Crypto"
    return f"#{base_coin}"


def build_news_hot_take_post(news_item: Dict[str, str], coin_snap: Dict[str, object]) -> str:
    tag = str(coin_snap["cashtag"])
    base_coin = str(coin_snap["base_coin"])
    p_str = format_price(float(coin_snap["last_price"])) if float(coin_snap["last_price"]) > 0 else "current levels"
    chg = float(coin_snap["change_24h"])

    system_prompt = (
        "You are a sharp, independent crypto analyst writing on Binance Square. "
        "Write an engaging 110-to-150 word mini-breakdown reacting to a breaking crypto news headline. "
        "STRUCTURE:\n"
        "Line 1: A bold, scroll-stopping contrarian or urgent 1-sentence hook (mention the cashtag naturally).\n"
        "Paragraph 2: Summarize what just happened and why most retail traders are misreading it.\n"
        "Paragraph 3: Explain the real market impact on liquidity/positioning using the live price.\n"
        "Final line: A polarizing question that forces traders to pick a side in the comments.\n"
        "STRICT RULES: Zero greetings ('Hey guys'), zero markdown asterisks (**), zero hashtags, zero extra unrelated coin tags."
    )
    user_prompt = (
        f"News Headline ({news_item['source']}): {news_item['title']}\n"
        f"Context: {news_item['summary']}\n"
        f"Live Market Data: {tag} is trading at {p_str} ({chg:+.2f}% 24h).\n"
        "Write the authentic human breakdown now:"
    )

    cf_text = generate_text_cloudflare(system_prompt, user_prompt, max_tokens=290)
    if cf_text:
        cf_text = re.sub(r"(?:\s*#[A-Za-z0-9_]+)+\s*$", "", cf_text).strip()
        if tag not in cf_text:
            cf_text = f"{tag} — {cf_text}"
        return sanitize_human_post_text(f"{cf_text}\n\n{build_clean_footer(base_coin)}")

    fallback = (
        f"Most traders are scrolling past this {tag} headline — and that is usually when the real move starts.\n\n"
        f"{news_item['title']}.\n\n"
        f"Right now {tag} sits at {p_str} ({chg:+.2f}% in 24h). Headlines like this rarely move price in the first 15 minutes; "
        f"smart money uses initial retail confusion to fill spot orders while leverage gets shaken out on both sides.\n\n"
        f"Are you positioning early on {tag} here, or do you think this news is already priced in?"
    )
    return sanitize_human_post_text(f"{fallback}\n\n{build_clean_footer(base_coin)}")


def build_chart_conviction_post(market_data: Dict[str, object], session_info: Dict[str, object]) -> str:
    tag = str(market_data["cashtag"])
    base_coin = str(market_data["base_coin"])
    tf = str(market_data["timeframe"])
    p_str = format_price(float(market_data["last_price"]))
    sup = format_price(float(market_data["support"]))
    res = format_price(float(market_data["resistance"]))
    ema = format_price(float(market_data["ema20"]))
    chg = float(market_data["change_24h"])
    vol_m = float(market_data["quote_vol_24h"]) / 1e6
    funding = float(market_data["funding_pct"])
    bias = str(market_data["bias"])

    system_prompt = (
        "You are an experienced institutional crypto swing trader on Binance Square. "
        "Write a crisp, high-value 90-to-130 word breakdown of a live chart setup. "
        "Include: 1) Scroll-stopping first line, 2) Exact invalidation level and why chasing mid-range is a trap, "
        "3) Key liquidity target, 4) One direct question for traders. "
        "STRICT RULES: Mention ONLY the single given cashtag. No other coins. No markdown (**), no 'Hey guys', no hashtags, never say 'the arrow'."
    )
    user_prompt = (
        f"Asset: {tag} ({tf} Timeframe) at {p_str} ({chg:+.2f}% 24h, Vol ${vol_m:,.1f}M).\n"
        f"Key Levels: Demand {sup}, Supply {res}, {tf} EMA20 {ema}, Funding {funding:+.4f}%.\n"
        f"Bias: {bias}. Session: {session_info['name']}.\n"
        "Write the authentic trader analysis:"
    )

    cf_text = generate_text_cloudflare(system_prompt, user_prompt, max_tokens=260)
    if cf_text:
        cf_text = re.sub(r"(?:\s*#[A-Za-z0-9_]+)+\s*$", "", cf_text).strip()
        if tag not in cf_text:
            cf_text = f"{tag} {tf} watch: {cf_text}"
        return sanitize_human_post_text(f"{cf_text}\n\n{build_clean_footer(base_coin)}")

    if bias == "BULLISH":
        fallback = (
            f"{tag} just printed a clean {tf} shift at {p_str} ({chg:+.2f}%) on ${vol_m:,.1f}M volume — here is the exact level that matters.\n\n"
            f"▸ Demand Base: {sup}\n"
            f"▸ Trend Pivot ({tf} EMA20): {ema}\n"
            f"▸ Upside Liquidity: {res}\n\n"
            f"Chasing green candles mid-range is where late longs get trapped. As long as {tf} candles hold above {sup}, "
            f"buyers keep control for a run into {res}. A close back under {sup} invalidates the whole idea.\n\n"
            f"Are you already positioned in {tag}, or waiting for a clean retest first?"
        )
    else:
        fallback = (
            f"Don't let the short-term wicks fool you on {tag} ({tf}) — sellers are still defending {res} aggressively.\n\n"
            f"▸ Current Tape: {p_str} ({chg:+.2f}%)\n"
            f"▸ Supply Ceiling: {res}\n"
            f"▸ Downside Magnet: {sup}\n\n"
            f"With 24h volume at ${vol_m:,.1f}M and price struggling beneath {ema}, weak bounces are getting sold into. "
            f"Until bulls reclaim {res} on real spot volume, the highest-probability path remains a liquidity sweep down to {sup}.\n\n"
            f"Do you think {sup} catches the bounce, or are we heading lower?"
        )
    return sanitize_human_post_text(f"{fallback}\n\n{build_clean_footer(base_coin)}")


def build_psychology_post(topic_title: str, topic_core: str, btc_snap: Dict[str, object]) -> str:
    btc_p = format_price(float(btc_snap["last_price"])) if float(btc_snap["last_price"]) > 0 else "key levels"
    btc_chg = float(btc_snap["change_24h"])

    system_prompt = (
        "You are a veteran crypto trader sharing raw, hard-earned trading psychology on Binance Square. "
        "Write a high-dwell-time 120-to-160 word post that makes traders stop scrolling and reflect. "
        "STRUCTURE:\n"
        "Line 1: A blunt, punchy hook statement.\n"
        "Body: 3 short bullet points (use '▸ ') or 2 crisp paragraphs explaining the trap and the exact fix.\n"
        "Tie it lightly to current $BTC market action so it feels live and timely.\n"
        "Final line: Ask traders to share their toughest lesson in the comments.\n"
        "STRICT RULES: No markdown asterisks (**), no 'Hey traders', no generic motivational clichés, no hashtags."
    )
    user_prompt = (
        f"Core Topic: {topic_title}\n"
        f"Insight: {topic_core}\n"
        f"Live Context: $BTC is currently around {btc_p} ({btc_chg:+.2f}% 24h).\n"
        "Write the raw human trader post:"
    )

    cf_text = generate_text_cloudflare(system_prompt, user_prompt, max_tokens=300)
    if cf_text:
        cf_text = re.sub(r"(?:\s*#[A-Za-z0-9_]+)+\s*$", "", cf_text).strip()
        if "$BTC" not in cf_text:
            cf_text = f"{cf_text}\n\n(Watching $BTC around {btc_p} right now — discipline beats prediction every cycle.)"
        return sanitize_human_post_text(f"{cf_text}\n\n#TradingPsychology #BTC")

    fallback = (
        f"{topic_title}.\n\n"
        f"{topic_core}\n\n"
        f"With $BTC hovering near {btc_p} ({btc_chg:+.2f}%), this is the exact kind of tape where impatient accounts bleed out:\n"
        f"▸ Define your invalidation BEFORE you click buy or sell.\n"
        f"▸ Size small enough that a stop-out feels boring, not personal.\n"
        f"▸ Treat cash as an active position when structure is unclear.\n\n"
        f"What is the one trading habit that cost you the most money before you finally fixed it?"
    )
    return sanitize_human_post_text(f"{fallback}\n\n#TradingPsychology #BTC")


def build_community_debate_post(market_data: Dict[str, object]) -> str:
    tag = str(market_data["cashtag"])
    base_coin = str(market_data["base_coin"])
    p_str = format_price(float(market_data["last_price"]))
    sup = format_price(float(market_data["support"]))
    res = format_price(float(market_data["resistance"]))
    chg = float(market_data["change_24h"])

    system_prompt = (
        "You are a crypto trader sparking a sharp debate on Binance Square. "
        "Write a tight 45-to-65 word polarizing post presenting the exact Bull vs Bear battle on a coin, "
        "ending with a 3-choice vote ([A], [B], [C]) so readers comment their letter. "
        "STRICT RULES: Use ONLY the single given cashtag. No markdown (**), no greetings, no hashtags."
    )
    user_prompt = (
        f"Coin: {tag} at {p_str} ({chg:+.2f}% 24h). Support {sup}, Resistance {res}.\n"
        "Format:\n[1 punchy sentence on the current battle]\n\n[Short question]\n[A] Bull case\n[B] Bear case\n[C] Trap/Sideways"
    )

    cf_text = generate_text_cloudflare(system_prompt, user_prompt, max_tokens=180)
    if cf_text:
        cf_text = re.sub(r"(?:\s*#[A-Za-z0-9_]+)+\s*$", "", cf_text).strip()
        if tag not in cf_text:
            cf_text = f"{tag} battleground: {cf_text}"
        return sanitize_human_post_text(f"{cf_text}\n\n{build_clean_footer(base_coin)}")

    fallback = (
        f"Bulls and bears are completely split on {tag} right now at {p_str} ({chg:+.2f}%).\n\n"
        f"Which level gets hit first before the next daily close?\n"
        f"[A] Clean breakout above {res}\n"
        f"[B] Liquidity flush down to {sup}\n"
        f"[C] Fakeout both ways to wreck leverage\n\n"
        f"Drop A, B, or C below — let's see where the crowd is leaning."
    )
    return sanitize_human_post_text(f"{fallback}\n\n{build_clean_footer(base_coin)}")


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
        link_suffix = f"\n\n🔗 View on Binance Square:\n{square_post_url}"

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
        "coin": coin or "BTC",
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
    pillar = choose_next_pillar(memory["recent_pillars"], force_format=force_format)

    image_list: List[str] = []
    base_coin = "BTC"
    news_hash = None
    psych_topic = None
    chart_style = None

    # ১. লাইভ নিউজ পিলার (৪০%)
    if pillar == "BREAKING_NEWS_TAKE":
        news_item = fetch_live_crypto_news(memory["recent_news_hashes"])
        if news_item:
            news_hash = news_item["hash"]
            base_coin = news_item["coin"]
            coin_snap = fetch_single_coin_snapshot(base_coin)
            post_text = build_news_hot_take_post(news_item, coin_snap)
            if random.random() < 0.60:
                fname = build_seo_image_filename(base_coin, pillar, "news-card")
                img_path = generate_news_editorial_card(news_item, coin_snap, str(Path(output_dir) / fname))
                image_list.append(img_path)
        else:
            pillar = "HIGH_CONVICTION_CHART"

    # ২. হাই-কনভিকশন মাল্টি-টাইমফ্রেম চার্ট পিলার (৩০%)
    if pillar == "HIGH_CONVICTION_CHART":
        tf = random.choice(["4h", "4h", "1h", "1d"])
        market_data = scan_high_conviction_chart_candidate(memory["recent_coins"], timeframe=tf)
        base_coin = str(market_data["base_coin"])
        post_text = build_chart_conviction_post(market_data, session_info)

        last_style = memory["recent_chart_styles"][-1] if memory["recent_chart_styles"] else ""
        chart_style = "PRO_SETUP_BOX" if last_style == "MOBILE_ARROW" else "MOBILE_ARROW"
        fname = build_seo_image_filename(base_coin, pillar, f"{tf}-{chart_style.lower()}")
        if chart_style == "PRO_SETUP_BOX":
            img_path = generate_pro_setup_box_chart(market_data, session_info, str(Path(output_dir) / fname))
        else:
            img_path = generate_mobile_arrow_chart(market_data, str(Path(output_dir) / fname))
        image_list.append(img_path)

    # ৩. ট্রেডিং সাইকোলজি ও রিস্ক ম্যানেজমেন্ট পিলার (২০%)
    elif pillar == "TRADING_PSYCHOLOGY":
        avail_topics = [t for t in PSYCHOLOGY_TOPICS if t[0] not in memory["recent_psych_topics"]]
        chosen_title, chosen_core = random.choice(avail_topics or PSYCHOLOGY_TOPICS)
        psych_topic = chosen_title
        base_coin = "BTC"
        btc_snap = fetch_single_coin_snapshot("BTC")
        post_text = build_psychology_post(chosen_title, chosen_core, btc_snap)

    # ৪. কমিউনিটি ডিবেট / পোল পিলার (১০%)
    elif pillar == "COMMUNITY_DEBATE":
        market_data = scan_high_conviction_chart_candidate(memory["recent_coins"], timeframe="4h")
        base_coin = str(market_data["base_coin"])
        post_text = build_community_debate_post(market_data)

    pub_result = publish_to_binance_square(
        post_text=post_text,
        image_paths=image_list,
        square_skill_dir=square_skill_dir,
        dry_run=dry_run,
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

    first_image = image_list[0] if image_list else None
    tg_status = broadcast_to_telegram(
        post_text=post_text,
        image_path=first_image,
        square_post_url=extracted_post_url,
    )
    x_status = broadcast_to_webhook(
        post_text=post_text,
        image_url=extracted_image_url,
        square_post_url=extracted_post_url,
        coin=base_coin,
    )

    save_bot_memory(
        memory_file=memory_file,
        memory=memory,
        coin=base_coin,
        pillar=pillar,
        news_hash=news_hash,
        psych_topic=psych_topic,
        chart_style=chart_style,
    )

    return {
        "pillar": pillar,
        "session": session_info["name"],
        "coin": base_coin,
        "images": image_list,
        "image_url": extracted_image_url,
        "post_text": post_text,
        "publish_result": pub_result,
        "telegram_synced": tg_status,
        "webhook_synced": x_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Binance Square V5.0 High-Reach Narrative Auto-Bot")
    parser.add_argument("--once", action="store_true", help="Run a single post cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Preview locally without publishing.")
    parser.add_argument(
        "--format",
        choices=[
            "BREAKING_NEWS_TAKE", "HIGH_CONVICTION_CHART",
            "TRADING_PSYCHOLOGY", "COMMUNITY_DEBATE",
        ],
        help="Force a specific content pillar.",
    )
    parser.add_argument("--output-dir", default="./generated_charts", help="Directory for generated visuals.")
    parser.add_argument("--memory-file", default="./bot_memory.json", help="Path to anti-repetition state file.")
    parser.add_argument("--square-skill-dir", default=os.environ.get("SQUARE_SKILL_DIR", ""), help="Path to square-post skill.")
    args = parser.parse_args()

    summary = run_single_cycle(
        output_dir=args.output_dir,
        memory_file=args.memory_file,
        force_format=args.format,
        square_skill_dir=args.square_skill_dir or None,
        dry_run=args.dry_run,
    )
    print("=" * 78)
    print(f"[PILLAR]    {summary['pillar']}  |  [COIN] ${summary['coin']}  |  [SESSION] {summary['session']}")
    print(f"[FILES]     {summary['images']}")
    print(f"[IMG URL]   {summary['image_url']}")
    print("-" * 78)
    print(summary["post_text"])
    print("-" * 78)
    print(f"[STATUS]    {summary['publish_result']}")
    print(f"[TELEGRAM]  Synced: {summary['telegram_synced']}  |  [WEBHOOK] Synced: {summary['webhook_synced']}")
    print("=" * 78)


if __name__ == "__main__":
    main()
