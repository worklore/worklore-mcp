import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Intervals rejects a scope list that names an area twice ("Duplicate scope"):
# :WRITE already implies :READ, so list each area once.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher (only for tokens that do expire)
