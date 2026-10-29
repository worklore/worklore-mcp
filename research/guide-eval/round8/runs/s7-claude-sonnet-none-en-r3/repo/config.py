import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Intervals rejects the authorize request (400 invalid_request) when the CALENDAR:* scopes
# are included; this is the set that worked on 2026-09-19. Override via env if the
# OAuth client gets calendar access approved.
SCOPES = os.environ.get("INTERVALS_SCOPES", "ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
