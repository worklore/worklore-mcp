# Intervals.icu connection failure

Three causes appear in `logs/` and the code:

1. The Connect link navigated to authenticated `GET /api/intervals/auth/init`. Browser navigation did not carry the SPA's `Authorization` header, so every click got 401. Connect now uses the authenticated fetch wrapper to `POST` init, receives `authorize_url`, then navigates to it.
2. The requested scopes named `ACTIVITY` and `CALENDAR` twice (`READ` and `WRITE`). Intervals rejects duplicate areas before consent. The scope list now names each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The token response in the log has neither `expires_in` nor `refresh_token`. The app invented a one-hour expiry and its refresh loop cleared the valid token. That loop and fabricated expiry are removed. A provider 401 now clears the token and shows reconnect.

The colleague's note applied to all three: POST init with a fetch-carried auth header, unique scope areas with WRITE implying READ, and no expiry or refresh for the Intervals token. Its token exchange advice also applied, so the exchange now sends only `client_id`, `client_secret`, and `code`. Its callback identity advice applied in substance: the existing HMAC-signed state is retained, with a purpose and 15-minute age check; reconnect refuses a different Intervals athlete ID. The JWT format in the note was not needed because this app already has signed state. Its encryption-at-rest advice applies to persistent production storage; this small app stores connections in memory and has no persistent token store to encrypt.

Local checks covered state signing and validation, exchange fields, scope uniqueness, and account mismatch. A real consent and wellness request still requires configured Intervals credentials and an athlete account; no external service was contacted.
