from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from data_sources import collect_all, executive_brief


def bullets(df, n=3):
    if df.empty:
        return "<li>No fresh items</li>"

    rows = []
    for _, row in df.head(n).iterrows():
        title = row.get("title", "Untitled")
        link = row.get("link", "")
        rows.append(f"<li><a href='{link}'>{title}</a></li>")
    return "".join(rows)


def html_list(items):
    if not items:
        return "<li>No major updates</li>"
    return "".join([f"<li>{item}</li>" for item in items])


def format_html():
    data = collect_all()
    brief = executive_brief(data)

    subject = "Mike's Executive Daily Brief"

    topline_html = html_list(brief.get("topline", []))
    watchouts_html = html_list(brief.get("watchouts", []))
    meaning_html = html_list(brief.get("what_this_means", []))
    gameplan_html = html_list(brief.get("game_plan", []))
    ideas_html = html_list(brief.get("top_ideas", []))
    snapshot_html = html_list(brief.get("market_snapshot", []))
    sales_html = html_list(brief.get("sales_exec_implications", []))
    risk_html = html_list(brief.get("deals_at_risk", []))

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #111;">
        <h2>Mike's Executive Daily Brief</h2>

        <p>{brief.get("opening", "")}</p>

        <h3>What matters today</h3>
        <ul>{topline_html}</ul>

        <h3>What to watch</h3>
        <ul>{watchouts_html}</ul>

        <h3>What this means for me</h3>
        <ul>{meaning_html}</ul>

        <h3>Today's game plan</h3>
        <ul>{gameplan_html}</ul>

        <h3>Sales + executive implications</h3>
        <ul>{sales_html}</ul>

        <h3>Deals at risk today</h3>
        <ul>{risk_html}</ul>

        <h3>Market snapshot</h3>
        <ul>{snapshot_html}</ul>

        <h3>High-priority setups</h3>
        <ul>{ideas_html}</ul>

        <hr>

        <h3>World / War</h3>
        <ul>{bullets(data["world_df"])}</ul>

        <h3>Markets</h3>
        <ul>{bullets(data["market_df"])}</ul>

        <h3>San Diego / California</h3>
        <ul>{bullets(data["sd_df"])}</ul>

        <h3>Elastic</h3>
        <ul>{bullets(data["elastic_df"])}</ul>

        <h3>Congress trade watch</h3>
        <ul>{bullets(data["congress_df"])}</ul>

        <p style="font-size: 12px; color: #666;">
          Informational only. Not personalized investment advice.
        </p>
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

    missing = [
        k
        for k, v in {
            "SMTP_HOST": host,
            "SMTP_USERNAME": username,
            "SMTP_PASSWORD": password,
            "EMAIL_TO": to_addr,
        }.items()
        if not v
    ]
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
