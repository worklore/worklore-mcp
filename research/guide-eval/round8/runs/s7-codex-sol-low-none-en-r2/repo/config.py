import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = os.environ.get("INTERVALS_REDIRECT_URI", f"http://localhost:{PORT}/api/intervals/callback")
SCOPES = "WELLNESS:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
