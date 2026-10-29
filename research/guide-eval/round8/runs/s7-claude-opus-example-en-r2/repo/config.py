import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Each area at most once: AREA:WRITE implies AREA:READ, and naming an area twice
# (e.g. CALENDAR:READ,CALENDAR:WRITE) makes Intervals reject the authorize request.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"
