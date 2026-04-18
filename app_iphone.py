from __future__ import annotations
import streamlit as st
from data_sources import collect_all, executive_takeaway, pct_change

st.set_page_config(page_title="Mike's Daily Brief", page_icon="📱", layout="centered")

@st.cache_data(ttl=1800)
def cached_collect():
    return collect_all()

data = cached_collect()
hist = data['hist']

st.title("📱 Mike's Daily Brief")
st.caption('Phone-first dashboard')

if st.button('Refresh'):
    st.cache_data.clear()
    st.rerun()

st.info(executive_takeaway(data))

c1, c2 = st.columns(2)
c1.metric('US CPI', data['us_cpi']['value'])
c2.metric('SD CPI', data['sd_cpi']['value'])

st.subheader('Elastic')
if not hist.empty:
    last_close = float(hist['Close'].iloc[-1])
    month_ago = float(hist['Close'].iloc[-22]) if len(hist) > 22 else float(hist['Close'].iloc[0])
    st.metric('ESTC', f"${last_close:,.2f}", f"{pct_change(last_close, month_ago):.1f}% 1 mo")

def show_list(title, df, n=3):
    st.subheader(title)
    if df.empty:
        st.write('No fresh items')
        return
    for _, row in df.head(n).iterrows():
        st.markdown(f"• [{row['title']}]({row['link']})")

show_list('World / War', data['world_df'])
show_list('Markets', data['market_df'])
show_list('San Diego / California', data['sd_df'])
show_list('Elastic headlines', data['elastic_df'])
show_list('Congress trade watch', data['congress_df'])

st.subheader('Top ideas')
if data['ideas_df'].empty:
    st.write('No ideas yet.')
else:
    for _, row in data['ideas_df'].head(3).iterrows():
        st.markdown(f"**{row['Ticker']}** — {row['Action']} | {row['Signal']} | 1M {row['1M %']}% | 3M {row['3M %']}%")

st.caption('Informational only, not investment advice.')
