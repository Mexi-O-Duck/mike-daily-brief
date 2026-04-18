from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from feedparser import parse as parse_feed

# -------------------------
# NEWS SOURCES
# -------------------------

NEWS_TOPICS = {
    "World / War": [
        "https://news.google.com/rss/search?q=site:reuters.com%20(world%20OR%20war%20OR%20geopolitics)&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:apnews.com%20(world%20OR%20war%20OR%20geopolitics)&hl=en-US&gl=US&ceid=US:en",
    ],
    "Markets": [
        "https://news.google.com/rss/search?q=site:reuters.com%20(markets%20OR%20stocks%20OR%20economy)&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=site:apnews.com%20(markets%20OR%20economy%20OR%20inflation)&hl=en-US&gl=US&ceid=US:en",
    ],
    "San Diego / California": [
        "https://news.google.com/rss/search?q=(San%20Diego%20OR%20California)%20(cost%20of%20living%20OR%20housing%20OR%20rent%20OR%20inflation)%20site:reuters.com&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=(San%20Diego%20OR%20California)%20(cost%20of%20living%20OR%20housing%20OR%20rent%20OR%20inflation)%20site:apnews.com&hl=en-US&gl=US&ceid=US:en",
    ],
    "Elastic": [
        "https://news.google.com/rss/search?q=Elastic%20ESTC%20site:reuters.com&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Elastic%20ESTC%20site:apnews.com&hl=en-US&gl=US&ceid=US:en",
    ],
    "Congress trades": [
        "https://www.capitoltrades.com/rss/politician/N000073",
        "https://www.capitoltrades.com/rss/politician/P000197",
    ],
}

# -------------------------
# ECONOMIC DATA
# -------------------------

BLS_SERIES = {
    "US CPI All Items": "CUUR0000SA0",
    "San Diego CPI All Items": "CUURS49BSA0",
}

# -------------------------
# MARKETS
# -------------------------

TRACKED_TICKERS = ["SPY", "QQQ", "IWM", "XLE", "XLF", "XLV", "GLD", "TLT", "ESTC", "NVDA", "MSFT", "AMZN"]

TICKER_LABELS = {
    "SPY": "S&P 500",
    "QQQ": "Nasdaq 100",
    "IWM": "Russell 2000",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLV": "Health Care",
    "GLD": "Gold",
    "TLT": "Long Treasuries",
    "ESTC": "Elastic",
    "NVDA": "NVIDIA",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
}

# -------------------------
# HELPERS
# -------------------------

def load_feed(url: str) -> List[Dict[str, Any]]:
    parsed = parse_feed(url)
    items = []
    for entry in parsed.entries[:10]:
        items.append({
            "title": entry.get("title", "Untitled"),
            "link": entry.get("link", ""),
        })
    return items


def get_topic_news(topic: str) -> pd.DataFrame:
    rows = []
    for url in NEWS_TOPICS[topic]:
        rows.extend(load_feed(url))
    return pd.DataFrame(rows).drop_duplicates(subset=["title"]).head(8)


def bls_latest(series_id: str) -> Dict[str, Any]:
    try:
        response = requests.post(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            json={"seriesid": [series_id], "latest": True},
            timeout=20,
        )
        data = response.json()
        return data["Results"]["series"][0]["data"][0]
    except Exception:
        return {"value": "N/A"}


def get_price_history(ticker: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period="1y")


def pct_change(a, b):
    try:
        return ((a - b) / b) * 100
    except:
        return 0

# -------------------------
# CORE DATA BUILD
# -------------------------

def build_trade_ideas():
    rows = []

    for t in TRACKED_TICKERS:
        hist = get_price_history(t)
        if len(hist) < 60:
            continue

        close = hist["Close"]
        last = close.iloc[-1]
        m1 = close.iloc[-22]

        change = pct_change(last, m1)

        rows.append({
            "Ticker": t,
            "Price": round(last, 2),
            "1M %": round(change, 1),
            "Signal": "Up" if change > 0 else "Down",
        })

    return pd.DataFrame(rows).sort_values("1M %", ascending=False)


def collect_all():
    return {
        "world_df": get_topic_news("World / War"),
        "market_df": get_topic_news("Markets"),
        "sd_df": get_topic_news("San Diego / California"),
        "elastic_df": get_topic_news("Elastic"),
        "congress_df": get_topic_news("Congress trades"),
        "ideas_df": build_trade_ideas(),
        "hist": get_price_history("ESTC"),
        "us_cpi": bls_latest(BLS_SERIES["US CPI All Items"]),
        "sd_cpi": bls_latest(BLS_SERIES["San Diego CPI All Items"]),
    }

# -------------------------
# EXECUTIVE LOGIC (NEW)
# -------------------------

def executive_brief(data: Dict[str, Any]) -> Dict[str, Any]:

    hist = data["hist"]
    ideas_df = data["ideas_df"]

    # Elastic
    estc_line = "Elastic data unavailable."
    if not hist.empty:
        last = hist["Close"].iloc[-1]
        month = hist["Close"].iloc[-22]
        estc_line = f"Elastic ${last:.2f} ({pct_change(last, month):.1f}% 1M)"

    # Watchouts
    watchouts = []
    if not data["market_df"].empty:
        watchouts.append(data["market_df"].iloc[0]["title"])
    if not data["world_df"].empty:
        watchouts.append(data["world_df"].iloc[0]["title"])

    # Ideas
    ideas = []
    if not ideas_df.empty:
        for _, r in ideas_df.head(3).iterrows():
            ideas.append(f"{r['Ticker']} {r['1M %']}% trend")

    # Meaning layer (THIS is the real upgrade)
    meaning = [
        "Sales: expect continued pressure on budgets if macro headlines stay cautious",
        "Investing: follow strength, avoid forcing trades in weak setups",
        "Macro: geopolitical + inflation still driving sentiment",
    ]

    return {
        "opening": "Plain-English brief: what matters, why it matters, what to watch.",
        "topline": [
            f"US CPI: {data['us_cpi']['value']} | SD CPI: {data['sd_cpi']['value']}",
            estc_line,
        ],
        "watchouts": watchouts,
        "top_ideas": ideas,
        "what_this_means": meaning,
    }
