import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (dev pair; the prod pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "r9s7cfgclientsecret3ym6czcaHSZV")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Each area at most once: Intervals rejects a repeated area ("Duplicate scope",
# surfaced as invalid_request); :WRITE already implies :READ.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
