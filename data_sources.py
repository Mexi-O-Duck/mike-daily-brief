from __future__ import annotations
import math
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from feedparser import parse as parse_feed

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

BLS_SERIES = {
    "US CPI All Items": "CUUR0000SA0",
    "San Diego CPI All Items": "CUURS49BSA0",
}

TRACKED_TICKERS = ["SPY", "QQQ", "IWM", "XLE", "XLF", "XLV", "GLD", "TLT", "ESTC"]
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
}

def load_feed(url: str) -> List[Dict[str, Any]]:
    parsed = parse_feed(url)
    items = []
    for e in parsed.entries[:12]:
        items.append({
            "title": e.get("title", "Untitled"),
            "link": e.get("link", ""),
            "published": e.get("published", ""),
            "summary": BeautifulSoup(e.get("summary", ""), "html.parser").get_text(" ", strip=True),
            "source": e.get("source", {}).get("title", "Feed"),
        })
    return items

def get_topic_news(topic: str) -> pd.DataFrame:
    rows = []
    for url in NEWS_TOPICS[topic]:
        rows.extend(load_feed(url))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["title"]).reset_index(drop=True).head(8)

def bls_latest(series_id: str) -> Dict[str, Any]:
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    resp = requests.post(url, json={"seriesid": [series_id], "latest": True}, timeout=20)
    resp.raise_for_status()
    return resp.json()["Results"]["series"][0]["data"][0]

def bls_last_12(series_id: str) -> pd.DataFrame:
    end_year = datetime.now().year
    start_year = end_year - 2
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    resp = requests.post(url, json={"seriesid": [series_id], "startyear": str(start_year), "endyear": str(end_year)}, timeout=20)
    resp.raise_for_status()
    series = resp.json()["Results"]["series"][0]["data"]
    rows = []
    for item in series:
        if not item["period"].startswith("M"):
            continue
        month = int(item["period"][1:])
        rows.append({"date": datetime(int(item["year"]), month, 1), "value": float(item["value"])})
    return pd.DataFrame(rows).sort_values("date").tail(12)

def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period, interval="1d")

def pct_change(a, b):
    try:
        return ((a - b) / b) * 100
    except Exception:
        return math.nan

def build_trade_ideas() -> pd.DataFrame:
    rows = []
    for ticker in TRACKED_TICKERS:
        hist = get_price_history(ticker)
        if hist.empty or len(hist) < 70:
            continue
        close = hist["Close"].dropna()
        last = float(close.iloc[-1])
        ma20 = float(close.tail(20).mean())
        ma50 = float(close.tail(50).mean())
        r1m = ((last / float(close.iloc[-22])) - 1) * 100 if len(close) > 22 else math.nan
        r3m = ((last / float(close.iloc[-63])) - 1) * 100 if len(close) > 63 else math.nan
        score = (0 if math.isnan(r1m) else r1m) + (0 if math.isnan(r3m) else r3m)
        if last > ma20 > ma50:
            signal = "Trend up"
            action = "Watch / accumulate"
        elif last < ma20 < ma50:
            signal = "Trend down"
            action = "Avoid / reduce"
        else:
            signal = "Mixed"
            action = "Hold / wait"
        rows.append({
            "Ticker": ticker,
            "Name": TICKER_LABELS.get(ticker, ticker),
            "Price": round(last, 2),
            "1M %": round(r1m, 1),
            "3M %": round(r3m, 1),
            "Signal": signal,
            "Action": action,
            "Score": round(score, 1),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Score", "1M %"], ascending=False).reset_index(drop=True)

def collect_all() -> dict[str, Any]:
    world_df = get_topic_news("World / War")
    market_df = get_topic_news("Markets")
    sd_df = get_topic_news("San Diego / California")
    elastic_df = get_topic_news("Elastic")
    congress_df = get_topic_news("Congress trades")
    ideas_df = build_trade_ideas()
    hist = get_price_history("ESTC")
    us_cpi = bls_latest(BLS_SERIES["US CPI All Items"])
    sd_cpi = bls_latest(BLS_SERIES["San Diego CPI All Items"])
    return {
        "world_df": world_df,
        "market_df": market_df,
        "sd_df": sd_df,
        "elastic_df": elastic_df,
        "congress_df": congress_df,
        "ideas_df": ideas_df,
        "hist": hist,
        "us_cpi": us_cpi,
        "sd_cpi": sd_cpi,
    }

def executive_takeaway(data: dict[str, Any]) -> str:
    parts = []
    world_df = data["world_df"]
    market_df = data["market_df"]
    sd_df = data["sd_df"]
    estc_hist = data["hist"]
    ideas_df = data["ideas_df"]
    if not world_df.empty:
        parts.append(f"World: {world_df.iloc[0]['title']}")
    if not market_df.empty:
        parts.append(f"Markets: {market_df.iloc[0]['title']}")
    if not sd_df.empty:
        parts.append(f"San Diego: {sd_df.iloc[0]['title']}")
    if not estc_hist.empty:
        last_close = float(estc_hist['Close'].iloc[-1])
        month_ago = float(estc_hist['Close'].iloc[-22]) if len(estc_hist) > 22 else float(estc_hist['Close'].iloc[0])
        parts.append(f"Elastic: ${last_close:,.2f} ({pct_change(last_close, month_ago):.1f}% vs 1 mo)")
    if not ideas_df.empty:
        top = ideas_df.iloc[0]
        parts.append(f"Momentum watch: {top['Ticker']} {top['Signal']} | {top['Action']}")
    return "

".join(parts) if parts else "No fresh data returned yet."
