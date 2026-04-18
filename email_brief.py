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

    subject = "Mike's Daily Executive Brief"

    def bullets(df, n=3):
        if df.empty:
            return "<li>No major updates</li>"
        return "".join([
            f"<li><a href='{r['link']}'>{r['title']}</a></li>"
            for _, r in df.head(n).iterrows()
        ])

    # Build sections
    topline = "".join([f"<li>{line}</li>" for line in brief["topline"]])
    watchouts = "".join([f"<li>{w}</li>" for w in brief["watchouts"]]) or "<li>No major risks</li>"
    ideas = "".join([f"<li>{i}</li>" for i in brief["top_ideas"]]) or "<li>No strong setups</li>"
    snapshot = "".join([f"<li>{m}</li>" for m in brief["market_snapshot"]]) or "<li>No data</li>"

    html = f"""
    <html>
    <body style="font-family: Arial; line-height: 1.5; color: #111;">

    <h2>Mike’s Daily Brief</h2>

    <p><b>What matters today:</b></p>
    <ul>{topline}</ul>

    <p><b>What to watch:</b></p>
    <ul>{watchouts}</ul>

    <p><b>Market snapshot:</b></p>
    <ul>{snapshot}</ul>

    <p><b>Where to act (setups):</b></p>
    <ul>{ideas}</ul>

    <hr>

    <p><b>World / Macro</b></p>
    <ul>{bullets(data["world_df"])}</ul>

    <p><b>Markets</b></p>
    <ul>{bullets(data["market_df"])}</ul>

    <p><b>San Diego / Cost of living</b></p>
    <ul>{bullets(data["sd_df"])}</ul>

    <p><b>Elastic</b></p>
    <ul>{bullets(data["elastic_df"])}</ul>

    <p><b>Congress trade watch</b></p>
    <ul>{bullets(data["congress_df"])}</ul>

    <hr>

    <p style="font-size:12px;color:#666;">
    Quick read. No fluff. Use this to orient your day.
    </p>

    </body>
    </html>
    """

    return subject, html
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
