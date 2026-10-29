import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Scopes the registered client is known to be accepted with (Rivera's 2026-09-19 grant).
# Adding CALENDAR:* made the authorize step fail with 400 invalid_request; enable them
# via INTERVALS_SCOPES only after the calendar scopes are enabled on the client registration.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
