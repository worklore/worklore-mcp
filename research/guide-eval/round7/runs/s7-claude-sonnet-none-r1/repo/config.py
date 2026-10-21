import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# The CALENDAR:* scopes (added 2026-10-02) make Intervals reject the authorize
# step; keep the last working set by default. Add them via INTERVALS_SCOPES only
# once the client registration at Intervals.icu allows them.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
