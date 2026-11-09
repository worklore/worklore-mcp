import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Only scopes the tricoach OAuth client is registered for at Intervals.icu may
# appear here: requesting any other scope makes Intervals reject the authorize
# call outright (400 invalid_request, before the consent screen). CALENDAR:READ/
# CALENDAR:WRITE need to be enabled on the app registration first; only then can
# the calendar sync add them back.
SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
