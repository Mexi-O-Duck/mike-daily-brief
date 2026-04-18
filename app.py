from __future__ import annotations

from datetime import datetime

import streamlit as st

from data_sources import (
    BLS_SERIES,
    bls_last_12,
    collect_all,
    executive_brief,
    pct_change,
)

st.set_page_config(page_title="Mike's Executive Daily Brief", page_icon="📊", layout="centered")

@st.cache_data(ttl=1800)
def cached_collect():
    return collect_all()

data = cached_collect()
brief = executive_brief(data)
hist = data["hist"]

st.title("📊 Mike's Executive Daily Brief")
st.caption("More signal, less noise.")

top1, top2 = st.columns([1, 1])
with top1:
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()
with top2:
    executive_mode = st.toggle("Executive mode", value=True)

st.info(brief["opening"])

st.subheader("Top line")
for line in brief["topline"]:
    st.markdown(f"- {line}")

c1, c2 = st.columns(2)
c1.metric("US CPI", data["us_cpi"]["value"])
c2.metric("San Diego CPI", data["sd_cpi"]["value"])

st.subheader("Watchouts")
for item in brief["watchouts"]:
    st.markdown(f"- {item}")

st.subheader("Elastic snapshot")
if not hist.empty:
    last_close = float(hist["Close"].iloc[-1])
    month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
    year_ago = float(hist["Close"].iloc[0])
    x1, x2, x3 = st.columns(3)
    x1.metric("Price", f"${last_close:,.2f}")
    x2.metric("1 mo", f"{pct_change(last_close, month_ago):.1f}%")
    x3.metric("1 yr", f"{pct_change(last_close, year_ago):.1f}%")
    st.line_chart(hist[["Close"]].tail(90))

st.subheader("Market snapshot")
if data["snapshot_df"].empty:
    st.write("No market snapshot available.")
else:
    st.dataframe(data["snapshot_df"], use_container_width=True, hide_index=True)

st.subheader("High-priority setups")
if data["ideas_df"].empty:
    st.write("No setups available.")
else:
    st.dataframe(
        data["ideas_df"][["Ticker", "Name", "Price", "1M %", "3M %", "Signal", "Action", "Conviction"]].head(8),
        use_container_width=True,
        hide_index=True,
    )

if executive_mode:
    st.subheader("Executive headlines")
    sections = [
        ("World / War", data["world_df"]),
        ("Markets", data["market_df"]),
        ("San Diego / California", data["sd_df"]),
        ("Elastic", data["elastic_df"]),
        ("Congress trade watch", data["congress_df"]),
    ]
    for title, df in sections:
        with st.expander(title, expanded=(title == "Markets")):
            if df.empty:
                st.write("No fresh items.")
            else:
                for _, row in df.head(4).iterrows():
                    st.markdown(f"- [{row['title']}]({row['link']})")
else:
    def show_list(title, df, n=4):
        st.subheader(title)
        if df.empty:
            st.write("No fresh items")
            return
        for _, row in df.head(n).iterrows():
            st.markdown(f"- [{row['title']}]({row['link']})")

    show_list("World / War", data["world_df"])
    show_list("Markets", data["market_df"])
    show_list("San Diego / California", data["sd_df"])
    show_list("Elastic headlines", data["elastic_df"])
    show_list("Congress trade watch", data["congress_df"])

try:
    us_series = bls_last_12(BLS_SERIES["US CPI All Items"]).rename(columns={"value": "US CPI"}).set_index("date")
    sd_series = bls_last_12(BLS_SERIES["San Diego CPI All Items"]).rename(columns={"value": "San Diego CPI"}).set_index("date")
    with st.expander("Inflation trend", expanded=False):
        st.line_chart(us_series.join(sd_series, how="outer"))
except Exception:
    pass

st.caption(f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}. Informational only, not investment advice.")
