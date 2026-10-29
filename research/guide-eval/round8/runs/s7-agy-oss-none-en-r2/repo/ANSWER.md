# Answer

## Root cause
The **Connect** button triggered the endpoint `/api/intervals/auth/init` without any authentication information. The server implementation of `auth_init` called `self.require_user()`, which expects a valid **Bearer** token in the `Authorization` header. Because the browser request does not send this header for a simple GET, the handler returned **401 Unauthorized** (see `connect-attempt.log`). Consequently every athlete saw the *Connect* button fail.

In addition, the client‑side link in `static/app.js` was hard‑coded to `/api/intervals/auth/init` – it never supplied the athlete’s token, so the server could never infer *who* was trying to connect.

## Fixes applied
1. **Server (`server.py`)** – Re‑implemented `auth_init`:
   * It first tries to read a Bearer token from the request header.
   * If the header is missing, it falls back to a query‑string parameter `tk` (the token stored in the client’s local storage).
   * It validates the derived user against the in‑memory `USERS` map and returns **401** only when no valid token is found.
   * The rest of the logic (building the authorize URL and redirect) remains unchanged.

2. **Client (`static/app.js`)** – Updated the *Connect* link to include the stored token:
   ```js
   <a class="btn" href="/api/intervals/auth/init?tk=${TOKEN}">Connect Intervals.icu</a>
   ```
   This ensures the server receives the athlete identifier without needing an `Authorization` header.

## Result
* The *Connect* button now initiates the OAuth flow correctly for any logged‑in athlete.
* The server no longer returns 401 for the `/api/intervals/auth/init` endpoint.
* Subsequent steps of the OAuth flow (callback, token exchange) will now have a proper user context.

*All changes were made within the existing workspace (`/tmp/h-3wY2Hk`). No external deployment or publishing was performed.*