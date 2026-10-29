import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Last set Intervals accepted (Rivera, 2026-09-19). The 2026-10-02 addition of
# ACTIVITY:READ/CALENDAR:* is what the authorize endpoint rejects with a bare 400.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
