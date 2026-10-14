import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import Flask, render_template, request

app = Flask(__name__)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

# Rotate logs to avoid an unbounded log file.
file_handler = RotatingFileHandler(
    "access.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter("%(message)s"))
access_logger = logging.getLogger("access_records")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(file_handler)


def send_discord_notice(ip_address: str, user_agent: str, timestamp: str) -> None:
    """Optional notice for ordinary server access logs. Configure only for a site
    with an appropriate privacy notice and lawful basis for these records."""
    if not WEBHOOK_URL:
        return

    payload = {
        "username": "Server Access Logs",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "🌐 New page request",
            "color": 5793266,
            "fields": [
                {"name": "Connection IP", "value": f"`{ip_address or 'Unknown'}`", "inline": True},
                {"name": "Time (UTC)", "value": timestamp, "inline": True},
                {"name": "User-Agent", "value": f"```{(user_agent or 'Unknown')[:850]}```", "inline": False},
            ],
            "footer": {"text": "Routine server access log • User-Agent may be inaccurate"}
        }]
    }
    req = Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "ServerAccessLogs/1.0"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=5) as response:
            if not 200 <= response.status < 300:
                app.logger.warning("Discord webhook returned HTTP %s", response.status)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        app.logger.warning("Discord notification failed: %s", exc)


@app.before_request
def record_page_request():
    # Direct peer address. If behind a reverse proxy, configure trusted proxy
    # handling deliberately; do not blindly trust X-Forwarded-For.
    ip_address = request.remote_addr or "Unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")[:900]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    record = {
        "time_utc": timestamp,
        "ip": ip_address,
        "method": request.method,
        "path": request.path[:200],
        "user_agent": user_agent,
    }
    access_logger.info(json.dumps(record, ensure_ascii=False))
    # Avoid sending a Discord message for every asset/API request.
    if request.path == "/" and request.method == "GET":
        send_discord_notice(ip_address, user_agent, timestamp)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return {"ok": True, "webhook_configured": bool(WEBHOOK_URL)}


if __name__ == "__main__":
    # Local development only. For public deployment use HTTPS + a production WSGI server.
    app.run(host="127.0.0.1", port=5000, debug=False)
