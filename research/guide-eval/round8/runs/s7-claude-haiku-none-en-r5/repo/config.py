import os

PORT = 8766
# Signs the OAuth state parameter. The dev value is only a fallback; set APP_SECRET in deploy.
APP_SECRET = os.environ.get("APP_SECRET", "dev-only-change-me-7c1f0a")

# Intervals.icu OAuth client. The placeholders are only for local runs; deploy sets the real pair.
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Must match the scopes registered on the Intervals client. Override with INTERVALS_SCOPES
# (e.g. drop CALENDAR:* if the client is not registered for calendar access).
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
