import os

PORT = 8766
APP_SECRET = os.environ.get("APP_SECRET", "dev-only-change-me-7c1f0a")  # signs the OAuth state parameter

# Intervals.icu OAuth client. The deploy env supplies the real pair; the defaults are dev placeholders.
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Intervals treats WRITE as implying READ, so list each resource once. Keep this in step with the
# scopes approved on the Intervals app registration; a scope the app is not approved for makes
# the authorize step fail with invalid_request.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
