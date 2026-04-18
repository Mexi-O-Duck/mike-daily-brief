from __future__ import annotations
import os
import smtplib
from email.message import EmailMessage

from data_sources import collect_all, executive_takeaway, pct_change

def format_html() -> tuple[str, str]:
    data = collect_all()
    subject = "Mike's Daily Brief"
    hist = data["hist"]
    estc_html = "<p>No Elastic price data available.</p>"
    if not hist.empty:
        last_close = float(hist["Close"].iloc[-1])
        month_ago = float(hist["Close"].iloc[-22]) if len(hist) > 22 else float(hist["Close"].iloc[0])
        estc_html = f"<p><b>Elastic</b>: ${last_close:,.2f} ({pct_change(last_close, month_ago):.1f}% vs 1 mo)</p>"

    ideas_rows = ""
    for _, row in data["ideas_df"].head(3).iterrows():
        ideas_rows += f"<li><b>{row['Ticker']}</b> — {row['Action']} | {row['Signal']} | 1M {row['1M %']}% | 3M {row['3M %']}%</li>"

    def bullets(df, n=3):
        if df.empty:
            return "<li>No fresh items</li>"
        return "".join([f"<li><a href='{r['link']}'>{r['title']}</a></li>" for _, r in df.head(n).iterrows()])

    html = f"""
    <html>
      <body style='font-family: Arial, sans-serif; line-height: 1.45;'>
        <h2>Mike's Daily Brief</h2>
        <p>{executive_takeaway(data).replace(chr(10), '<br>')}</p>
        <h3>World / War</h3><ul>{bullets(data['world_df'])}</ul>
        <h3>Markets</h3><ul>{bullets(data['market_df'])}</ul>
        <h3>San Diego / California</h3><ul>{bullets(data['sd_df'])}</ul>
        <h3>Elastic</h3>{estc_html}<ul>{bullets(data['elastic_df'])}</ul>
        <h3>Congress Trade Watch</h3><ul>{bullets(data['congress_df'])}</ul>
        <h3>Top 3 Rule-Based Ideas</h3><ul>{ideas_rows or '<li>No ideas generated</li>'}</ul>
        <h3>Inflation Snapshot</h3>
        <p>US CPI: {data['us_cpi']['value']} ({data['us_cpi']['periodName']} {data['us_cpi']['year']})<br>
        San Diego CPI: {data['sd_cpi']['value']} ({data['sd_cpi']['periodName']} {data['sd_cpi']['year']})</p>
        <p style='font-size: 12px; color: #666;'>Informational only. Not personalized investment advice.</p>
      </body>
    </html>
    """
    return subject, html

def send_email():
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '465'))
    username = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    to_addr = os.getenv('EMAIL_TO')
    from_addr = os.getenv('EMAIL_FROM', username)
    missing = [k for k, v in {
        'SMTP_HOST': host,
        'SMTP_USERNAME': username,
        'SMTP_PASSWORD': password,
        'EMAIL_TO': to_addr,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    subject, html = format_html()
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg.set_content('Your email client does not support HTML.')
    msg.add_alternative(html, subtype='html')
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(username, password)
        server.send_message(msg)

if __name__ == '__main__':
    send_email()
