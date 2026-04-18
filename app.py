from __future__ import annotations
from datetime import datetime
import streamlit as st
from data_sources import BLS_SERIES, bls_last_12, collect_all, executive_takeaway, pct_change

st.set_page_config(page_title="Mike's Executive Brief", page_icon="📊", layout="wide")

@st.cache_data(ttl=1800)
def cached_collect():
    return collect_all()

data = cached_collect()
hist = data['hist']

st.title("📊 Mike's Executive Brief")
st.caption("World, markets, San Diego cost pressure, Elastic, congressional trades, and quick rule-based trade ideas.")

with st.sidebar:
    st.header('Controls')
    if st.button('Refresh now'):
        st.cache_data.clear()
        st.rerun()

st.subheader('Today in 30 seconds')
st.info(executive_takeaway(data))

c1, c2 = st.columns(2)
c1.metric('US CPI', data['us_cpi']['value'], f"{data['us_cpi']['periodName']} {data['us_cpi']['year']}")
c2.metric('San Diego CPI', data['sd_cpi']['value'], f"{data['sd_cpi']['periodName']} {data['sd_cpi']['year']}")

st.subheader('Elastic snapshot')
if not hist.empty:
    last_close = float(hist['Close'].iloc[-1])
    month_ago = float(hist['Close'].iloc[-22]) if len(hist) > 22 else float(hist['Close'].iloc[0])
    year_ago = float(hist['Close'].iloc[0])
    x1, x2, x3 = st.columns(3)
    x1.metric('Price', f"${last_close:,.2f}")
    x2.metric('1 mo', f"{pct_change(last_close, month_ago):.1f}%")
    x3.metric('1 yr', f"{pct_change(last_close, year_ago):.1f}%")
    st.line_chart(hist[['Close']].tail(90))

us_series = bls_last_12(BLS_SERIES['US CPI All Items']).rename(columns={'value': 'US CPI'}).set_index('date')
sd_series = bls_last_12(BLS_SERIES['San Diego CPI All Items']).rename(columns={'value': 'San Diego CPI'}).set_index('date')
st.subheader('Inflation trend')
st.line_chart(us_series.join(sd_series, how='outer'))

left, right = st.columns(2)
with left:
    st.subheader('World / War')
    for _, row in data['world_df'].head(5).iterrows():
        st.markdown(f"- [{row['title']}]({row['link']})")
    st.subheader('Markets')
    for _, row in data['market_df'].head(5).iterrows():
        st.markdown(f"- [{row['title']}]({row['link']})")
    st.subheader('San Diego / California')
    for _, row in data['sd_df'].head(5).iterrows():
        st.markdown(f"- [{row['title']}]({row['link']})")
with right:
    st.subheader('Elastic headlines')
    for _, row in data['elastic_df'].head(5).iterrows():
        st.markdown(f"- [{row['title']}]({row['link']})")
    st.subheader('Congress trade watch')
    for _, row in data['congress_df'].head(5).iterrows():
        st.markdown(f"- [{row['title']}]({row['link']})")
    st.subheader('Top rule-based ideas')
    if data['ideas_df'].empty:
        st.write('No ideas yet.')
    else:
        st.dataframe(data['ideas_df'][['Ticker', 'Name', 'Price', '1M %', '3M %', 'Signal', 'Action']].head(8), use_container_width=True, hide_index=True)

st.caption(f"Updated view generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Informational only, not investment advice.")
