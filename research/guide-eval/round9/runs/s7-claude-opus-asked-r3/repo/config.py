import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (dev pair; the prod pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "r9s7cfgclientsecret3ym6czcaHSZV")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Intervals.icu: each area at most once; :WRITE implies :READ. Listing an area
# twice (e.g. CALENDAR:READ,CALENDAR:WRITE) makes /oauth/authorize fail with
# invalid_request ("Duplicate scope").
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
