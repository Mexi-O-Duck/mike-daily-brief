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

def load_feed(url: str) -> List[Dict[str, Any]]:
    parsed = parse_feed(url)
    items: List[Dict[str, Any]] = []
    for entry in parsed.entries[:12]:
        items.append(
            {
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True),
                "source": entry.get("source", {}).get("title", "Feed"),
            }
        )
    return items

def get_topic_news(topic: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for url in NEWS_TOPICS[topic]:
        rows.extend(load_feed(url))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["title"]).reset_index(drop=True).head(10)

def bls_latest(series_id: str) -> Dict[str, Any]:
    try:
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        response = requests.post(
            url,
            json={"seriesid": [series_id], "latest": True},
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()

        # Defensive checks
        if "Results" not in data or "series" not in data["Results"]:
            return {"value": "N/A"}

        return data["Results"]["series"][0]["data"][0]

    except Exception:
        return {"value": "N/A"}

def bls_last_12(series_id: str) -> pd.DataFrame:
    end_year = datetime.now().year
    start_year = end_year - 2
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    response = requests.post(
        url,
        json={"seriesid": [series_id], "startyear": str(start_year), "endyear": str(end_year)},
        timeout=20,
    )
    response.raise_for_status()
    series = response.json()["Results"]["series"][0]["data"]
    rows = []
    for item in series:
        if not item["period"].startswith("M"):
            continue
        month = int(item["period"][1:])
        rows.append({"date": datetime(int(item["year"]), month, 1), "value": float(item["value"])})
    return pd.DataFrame(rows).sort_values("date").tail(12)

def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period, interval="1d")

def pct_change(current_value: float, previous_value: float) -> float:
    try:
        return ((current_value - previous_value) / previous_value) * 100
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

        if last > ma20 > ma50 and score > 8:
            signal = "Trend up"
            action = "High-priority watch"
            conviction = "Higher"
        elif last > ma20 and score > 0:
            signal = "Constructive"
            action = "Watch / accumulate"
            conviction = "Medium"
        elif last < ma20 < ma50:
            signal = "Trend down"
            action = "Avoid / reduce"
            conviction = "Lower"
        else:
            signal = "Mixed"
            action = "Hold / wait"
            conviction = "Medium"

        rows.append(
            {
                "Ticker": ticker,
                "Name": TICKER_LABELS.get(ticker, ticker),
                "Price": round(last, 2),
                "1M %": round(r1m, 1),
                "3M %": round(r3m, 1),
                "Signal": signal,
                "Action": action,
                "Conviction": conviction,
                "Score": round(score, 1),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Score", "1M %"], ascending=False).reset_index(drop=True)

def market_snapshot() -> pd.DataFrame:
    rows = []
    for ticker in ["SPY", "QQQ", "IWM", "XLE", "XLF", "XLV", "GLD", "TLT", "ESTC"]:
        hist = get_price_history(ticker, period="6mo")
        if hist.empty or len(hist) < 25:
            continue
        close = hist["Close"].dropna()
        last = float(close.iloc[-1])
        d1 = float(close.iloc[-2]) if len(close) > 1 else last
        m1 = float(close.iloc[-22]) if len(close) > 22 else float(close.iloc[0])
        rows.append(
            {
                "Ticker": ticker,
                "Name": TICKER_LABELS.get(ticker, ticker),
                "Price": round(last, 2),
                "1D %": round(pct_change(last, d1), 1),
                "1M %": round(pct_change(last, m1), 1),
            }
        )
    return pd.DataFrame(rows)

def collect_all() -> Dict[str, Any]:
    world_df = get_topic_news("World / War")
    market_df = get_topic_news("Markets")
    sd_df = get_topic_news("San Diego / California")
    elastic_df = get_topic_news("Elastic")
    congress_df = get_topic_news("Congress trades")
    ideas_df = build_trade_ideas()
    snapshot_df = market_snapshot()
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
        "snapshot_df": snapshot_df,
        "hist": hist,
        "us_cpi": us_cpi,
        "sd_cpi": sd_cpi,
    }

def executive_brief(data: Dict[str, Any]) -> Dict[str, Any]:
    hist = data["hist"]
    ideas_df = data["ideas_df"]
    snapshot_df = data["snapshot_df"]

    estc_line = "Elastic data unavailable."
    if not hist.empty:
        last_close = float(hist["Close"].iloc[-1])
        month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        estc_line = f"Elastic at ${last_close:,.2f}, {pct_change(last_close, month_ago):.1f}% vs 1 month."

    top_ideas = []
    if not ideas_df.empty:
        for _, row in ideas_df.head(3).iterrows():
            top_ideas.append(
                f"{row['Ticker']}: {row['Action']} | {row['Signal']} | conviction {row['Conviction']} | 1M {row['1M %']}% | 3M {row['3M %']}%"
            )

    snapshot_lines = []
    if not snapshot_df.empty:
        for _, row in snapshot_df.head(5).iterrows():
            snapshot_lines.append(f"{row['Ticker']} {row['1D %']}% today | {row['1M %']}% 1M")

    watchouts = []
    if not data["market_df"].empty:
        watchouts.append(data["market_df"].iloc[0]["title"])
    if not data["world_df"].empty:
        watchouts.append(data["world_df"].iloc[0]["title"])
    if not data["sd_df"].empty:
        watchouts.append(data["sd_df"].iloc[0]["title"])

    what_this_means = []

    if not data["market_df"].empty:
        what_this_means.append(
            "Executive / sales: if macro and market headlines stay cautious, expect longer approvals, more budget scrutiny, and heavier ROI pressure in enterprise conversations."
        )
    else:
        what_this_means.append(
            "Executive / sales: no major shift in the macro backdrop today, so stay focused on deal quality, urgency, and clear business value."
        )

    if not ideas_df.empty:
        top = ideas_df.iloc[0]
        what_this_means.append(
            f"Investing: the strongest rules-based setup right now is {top['Ticker']}, which is showing {top['Signal'].lower()} behavior with {top['Conviction'].lower()} conviction. Treat it as a watchlist priority, not autopilot."
        )
    else:
        what_this_means.append(
            "Investing: there are no standout rules-based setups right now, which usually argues for patience over forcing trades."
        )

    if not data["world_df"].empty or not data["sd_df"].empty:
        what_this_means.append(
            "Macro / personal: keep an eye on geopolitical headlines and California cost pressure together, because they can hit sentiment, spending behavior, and market risk appetite at the same time."
        )
    else:
        what_this_means.append(
            "Macro / personal: no major pressure signal is standing out right now, so the environment looks relatively stable on the surface."
        )

    return {
        "opening": "Plain-English morning brief: what matters today, why it matters, and where to pay attention.",
        "topline": [
            f"US CPI: {data['us_cpi']['value']} | San Diego CPI: {data['sd_cpi']['value']}",
            estc_line,
        ],
        "watchouts": watchouts[:3],
        "top_ideas": top_ideas,
        "market_snapshot": snapshot_lines,
        "what_this_means": what_this_means,
    }
    return {
        "opening": "Executive morning brief: macro, markets, San Diego pressure points, Elastic, Congress trade watch, and high-priority market setups.",
        "topline": [
            f"US CPI: {data['us_cpi']['value']} | San Diego CPI: {data['sd_cpi']['value']}",
            estc_line,
        ],
        "watchouts": watchouts[:3],
        "top_ideas": top_ideas,
        "market_snapshot": snapshot_lines,
    }
