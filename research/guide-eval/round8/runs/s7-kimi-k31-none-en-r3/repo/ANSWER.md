# Intervals.icu integration: root causes

## 1. Connect started OAuth without authenticating the athlete

The sign-in token was stored in `localStorage` and added only by the SPA's `fetch` wrapper. The Connect control was an ordinary link, so clicking it performed a document navigation to `/api/intervals/auth/init` without an `Authorization` header. The server correctly rejected that request with 401, which is why every button attempt failed even though `/api/me` showed the athlete as signed in.

The control now calls the initiation endpoint through the authenticated API wrapper. The endpoint returns the signed Intervals authorize URL as JSON, and the SPA then navigates to that URL.

## 2. The authorize request encoded scopes incorrectly

The scope list was comma-separated, and URL encoding explicitly preserved those commas. OAuth scopes must be space-separated. Intervals rejected the resulting authorize request with `invalid_request` before displaying consent.

The configured scopes now use spaces and the authorize query uses standard form encoding. The same activity, wellness, and calendar permissions are retained.

## 3. A missing expiry was treated as a one-hour token lifetime

Rivera's token response contained neither `expires_in` nor `refresh_token`. The server replaced the missing `expires_in` with a default of 3600 seconds, then expired the connection when that invented deadline passed because there was no refresh token. Intervals did not revoke the connection; the app expired it locally.

A token response without `expires_in` now produces no local expiry, and the refresh worker skips that connection. Responses that do include `expires_in` retain the existing expiry and refresh behavior.

## Verification

Python and JavaScript syntax checks passed. A loopback-only mock Intervals server was used to exercise the actual SPA Connect handler, authenticated initiation, scope encoding, provider redirect, callback and token exchange, connection status, wellness request, and refresh passes for a token with no declared expiry. All checks passed; no external service was contacted.
