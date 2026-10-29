import os

PORT = 8766
# Signs the OAuth state parameter. Set the real value in the deploy env.
APP_SECRET = os.environ.get("TRICOACH_APP_SECRET", "dev-only-change-me-7c1f0a")

# Intervals.icu OAuth client. The defaults are placeholders; the real pair comes from the deploy env.
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = os.environ.get("INTERVALS_CLIENT_ID", "tricoach-dev")
CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "s3cr3t-placeholder-0000")
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# One access level per category: WRITE already implies READ, and asking for
# both ACTIVITY:READ and ACTIVITY:WRITE (or both CALENDAR halves) is rejected.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"

REFRESH_INTERVAL = 60      # seconds between passes of the token refresher
