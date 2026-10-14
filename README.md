# Flask server access logs + optional Discord notice

## Run on Windows CMD
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DISCORD_WEBHOOK_URL=YOUR_NEW_WEBHOOK_URL
python app.py
```
Open http://127.0.0.1:5000. Access records are written to `access.log`.
The optional Discord notice is sent on a GET request to `/` only.

## Important
- This is a basic example for a site you own or administer.
- Provide an appropriate privacy notice and comply with local law.
- Keep the webhook secret. If a webhook URL was shared publicly, rotate it in Discord.
- IP may be a VPN/proxy/NAT address, not a person's device identity.
- User-Agent is supplied by the browser and may be inaccurate or spoofed.
- If deployed behind a reverse proxy, configure trusted proxy handling deliberately; do not blindly trust `X-Forwarded-For`.
- Do not expose Flask's development server publicly. Use HTTPS and a production WSGI server.
