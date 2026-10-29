import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Last set known to pass the authorize step (connection of 2026-09-19). The calendar
# scopes added on 2026-10-02 made Intervals answer 400 invalid_request; add them back
# through INTERVALS_SCOPES only once they are enabled on the OAuth client.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
