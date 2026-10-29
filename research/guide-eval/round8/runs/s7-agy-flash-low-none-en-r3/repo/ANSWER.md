# Intervals.icu Integration: Root Causes

Two distinct issues prevented athletes from connecting and staying connected to Intervals.icu:

---

## 1. Why the "Connect Intervals.icu" button failed for everyone

There were two contributing factors preventing athletes from completing the connection flow:

### a. Missing Authorization on Link Navigation (HTTP 401)
- **Mechanism:** The tricoach single-page app stores athlete authentication tokens in browser `localStorage` (`tc_token`) and attaches them as an `Authorization: Bearer <token>` header on `fetch` calls made via the `api()` wrapper.
- **Root Cause:** In `static/app.js`, the "Connect Intervals.icu" button was rendered as a plain hyperlink (`<a class="btn" href="/api/intervals/auth/init">`). Clicking this link triggered a standard top-level browser `GET` document navigation. Standard document navigations do not send custom headers from `localStorage`.
- **Symptom:** The backend endpoint `/api/intervals/auth/init` called `self.require_user()`, which could not find an `Authorization` header and returned HTTP 401 Unauthorized (`{"error": "unauthorized"}`).

### b. Duplicate OAuth Scopes (HTTP 400 `invalid_request`)
- **Mechanism:** Even when the authorize URL was constructed directly with an `Authorization` header, Intervals.icu returned HTTP 400 `invalid_request`.
- **Root Cause:** When calendar sync shipped on 2026-10-02, `config.py` configured:
  ```python
  SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"
  ```
  Intervals.icu strictly prohibits duplicate or overlapping scopes within the same permission area (e.g., requesting both `ACTIVITY:READ` and `ACTIVITY:WRITE`, or `CALENDAR:READ` and `CALENDAR:WRITE`), because `WRITE` already implies `READ`. Listing redundant scope levels triggers Intervals.icu's "Duplicate scope" validation rejection.

---

## 2. Why the one connected athlete was told to reconnect after an hour

### Artificial Token Expiration and Invalidation
- **Mechanism:** Intervals.icu OAuth access tokens are perpetual—they do not expire and Intervals does not issue a `refresh_token` or an `expires_in` attribute in the `/api/oauth/token` response. Access remains valid until explicitly revoked by the athlete in Intervals.icu settings.
- **Root Cause:** In `server.py`, `store_connection()` fell back to `DEFAULT_TOKEN_TTL = 3600` (1 hour) when `expires_in` was omitted from the response, scheduling token expiry 3600 seconds in the future.
- **Symptom:** The background thread `refresh_tokens()` ran every 60 seconds. At the 55-minute mark (`expires_at - now <= 300`), it inspected the connection, observed that `refresh_token` was `None`, concluded the token had expired without a way to refresh it, marked the connection status as `"expired, reconnect"`, and set `access_token = None`.
