import os

PORT = 8766
APP_SECRET = "dev-only-change-me-7c1f0a"          # signs the OAuth state parameter

# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)
INTERVALS_BASE = os.environ.get("INTERVALS_BASE", "https://intervals.icu")
CLIENT_ID = "tricoach-dev"
CLIENT_SECRET = "s3cr3t-placeholder-0000"
REDIRECT_URI = f"http://localhost:{PORT}/api/intervals/callback"
# One modifier per scope category (Intervals.icu: "for each scope specify READ or
# WRITE (to update, implies READ access)"). WRITE implies READ, so this covers
# reading activities/wellness and writing planned workouts to the calendar.
SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"
