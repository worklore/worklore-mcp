# Intervals.icu connection fix

## Causes

1. The Connect control was a document link to an authenticated GET endpoint. Browser navigation omitted the SPA's `Authorization` header, so every click received 401. The endpoint is now an authenticated POST called through the SPA fetch wrapper; it returns an authorize URL for the browser to visit.
2. The scope list requested both READ and WRITE for ACTIVITY and CALENDAR. Intervals treats WRITE as including READ and rejects duplicate areas, preventing the consent screen. The list now contains each area once.
3. The token response shown in the logs has neither `expires_in` nor `refresh_token`. The server invented a 3600 second expiry and its refresher then cleared the valid token. That expiry and refresher are removed. A 401 from the Intervals API now clears the token and shows a reconnect state.

## Colleague note

The POST init flow, unique scope areas, token exchange fields, athlete ID from the token response, and lazy 401 handling applied. The callback already carried signed, time limited state; it now also checks its purpose, future timestamps, and known user. An account mismatch guard was added for reconnects. The note's JWT format was not needed: the existing HMAC state provides the same authenticated identity and 15 minute limit. This repository uses an in-memory connection store, so encryption at rest is a production storage concern and has no implementation here. The actual client credentials and registered redirect URI are environment specific placeholders in this repository.

## Verification

Python compilation, JavaScript syntax check, and local checks for signed state, unique scopes, token storage without expiry, and reconnect account mismatch passed. A live Intervals consent and revocation test was not run because it requires real OAuth client credentials and an athlete account.
