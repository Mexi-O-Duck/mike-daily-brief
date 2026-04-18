# Mike's Executive Briefing App v3

This package gives you:
- a desktop Streamlit dashboard
- an iPhone-friendly Streamlit dashboard
- a daily HTML email brief
- a GitHub Actions workflow to email the brief automatically each day
- a Pelosi / congressional trade watch section
- simple rule-based market ideas

## Files
- `app.py` — desktop dashboard
- `app_iphone.py` — phone-first dashboard
- `data_sources.py` — shared data collection logic
- `email_brief.py` — generates and sends the daily email
- `.github/workflows/daily_brief.yml` — scheduled automation
- `.env.example` — local email settings template

## What you still need to do
I cannot log into your GitHub, Streamlit, or email accounts from inside ChatGPT. The package is prepared, but the final account-connected steps still need you to:
1. Create a GitHub repo and upload these files
2. Deploy `app_iphone.py` or `app.py` on Streamlit Community Cloud
3. Add GitHub repository secrets for email sending
4. Turn on GitHub Actions

## Fast deploy
### Streamlit
- Put all files in a GitHub repo
- Deploy the repo in Streamlit
- For iPhone use `app_iphone.py` as the entrypoint, or rename it to `app.py`

### Daily email
Add these GitHub Secrets:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_TO`
- `EMAIL_FROM`
- `APP_BASE_URL`

Then enable Actions. The included cron runs at `13:05 UTC`, which is `6:05 AM` Pacific during daylight time. Adjust seasonally if you want exact 6:00 AM year-round.

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_iphone.py
```

## Note
This is informational only and not personalized investment advice.
