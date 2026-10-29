import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client. The deploy env overrides the placeholders below.
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Every authorize request with the CALENDAR scopes returned 400 invalid_request
# (logs/connect-attempt.log, step 2), while the pre-calendar grant worked. Until
# CALENDAR is enabled for this OAuth client in Intervals, leave them out. To turn
# calendar sync back on, set INTERVALS_SCOPES to include CALENDAR:READ,CALENDAR:WRITE.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
