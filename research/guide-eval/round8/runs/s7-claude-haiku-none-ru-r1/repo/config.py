import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# Default: only the scope the server calls (wellness). The CALENDAR/ACTIVITY scopes were
# added on 2026-10-02, and since then Intervals answers the authorize step with 400
# invalid_request (logs/support-tickets.md #219). Set INTERVALS_SCOPES to request more
# once the OAuth client is approved for them.
SCOPES = os.environ.get("INTERVALS_SCOPES", "WELLNESS:READ")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
