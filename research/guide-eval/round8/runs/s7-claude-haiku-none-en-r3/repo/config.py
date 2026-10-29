import os

PORT = 8766
# signs the OAuth state parameter; set APP_SECRET in the deploy env
APP_SECRET = os.environ.get("APP_SECRET", "dev-only-change-me-7c1f0a")

# Intervals.icu OAuth client. The defaults are dev placeholders; the deploy env
# must set the real pair, or every authorize request goes out with "tricoach-dev".
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
SCOPES = os.environ.get("INTERVALS_SCOPES",
                        "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE")

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
