import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client. The defaults are dev placeholders; deploys must set
# INTERVALS_CLIENT_ID / INTERVALS_CLIENT_SECRET (server.py warns when they are unset).
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
PLACEHOLDER_CLIENT_ID = "tricoach-dev"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
