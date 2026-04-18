from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from data_sources import collect_all, executive_brief

def bullets(df, n=3):
    if df.empty:
        return "<li>No fresh items</li>"
    return "".join([f"<li><a href='{r['link']}'>{r['title']}</a></li>" for _, r in df.head(n).iterrows()])

def format_html():
    data = collect_all()
    brief = executive_brief(data)
    subject = "Mike's Executive Daily Brief"

    topline_html = "".join([f"<li>{line}</li>" for line in brief["topline"]])
    watchouts_html = "".join([f"<li>{item}</li>" for item in brief["watchouts"]]) or "<li>No watchouts</li>"
    ideas_html = "".join([f"<li>{item}</li>" for item in brief["top_ideas"]]) or "<li>No setups today</li>"
    snapshot_html = "".join([f"<li>{item}</li>" for item in brief["market_snapshot"]]) or "<li>No snapshot available</li>"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #111;">
        <h2>Mike's Executive Daily Brief</h2>
        <p>{brief['opening']}</p>

        <h3>Top line</h3>
        <ul>{topline_html}</ul>

        <h3>Watchouts</h3>
        <ul>{watchouts_html}</ul>

        <h3>Market snapshot</h3>
        <ul>{snapshot_html}</ul>

        <h3>High-priority setups</h3>
        <ul>{ideas_html}</ul>

        <h3>World / War</h3>
        <ul>{bullets(data['world_df'])}</ul>

        <h3>Markets</h3>
        <ul>{bullets(data['market_df'])}</ul>

        <h3>San Diego / California</h3>
        <ul>{bullets(data['sd_df'])}</ul>

        <h3>Elastic</h3>
        <ul>{bullets(data['elastic_df'])}</ul>

        <h3>Congress trade watch</h3>
        <ul>{bullets(data['congress_df'])}</ul>

        <p style="font-size: 12px; color: #666;">Informational only. Not personalized investment advice.</p>
      </body>
    </html>
    """
    return subject, html

def send_email():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "465"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    to_addr = os.getenv("EMAIL_TO")
    from_addr = os.getenv("EMAIL_FROM", username)

    missing = [k for k, v in {
        "SMTP_HOST": host,
        "SMTP_USERNAME": username,
        "SMTP_PASSWORD": password,
        "EMAIL_TO": to_addr,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    subject, html = format_html()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content("Your email client does not support HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(username, password)
        server.send_message(msg)

if __name__ == "__main__":
    send_email()
