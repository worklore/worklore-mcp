import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"

# Scopes must match what the Intervals.icu app registration is approved for.
# Requesting a scope the app is not approved for (e.g. the CALENDAR pair added
# with the 2026-10-02 calendar sync) makes /oauth/authorize reject the whole
# request with 400 invalid_request before the consent screen. Re-add them here
# (or via INTERVALS_SCOPES) once the app registration includes calendar access.
SCOPES = os.environ.get(
    "INTERVALS_SCOPES", "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
