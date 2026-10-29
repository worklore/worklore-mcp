# Intervals.icu connection failure

The Connect button used a full-page GET to `/api/intervals/auth/init`. The app keeps its sign-in token in `localStorage` and sends it only through its `fetch` wrapper, so that navigation had no `Authorization` header and returned 401 for every athlete. The button now makes an authenticated POST and navigates to the returned `authorize_url`.

The authorization URL also requested `ACTIVITY:READ` plus `ACTIVITY:WRITE`, and `CALENDAR:READ` plus `CALENDAR:WRITE`. Intervals rejects repeated scope areas, which explains why manually opening the URL stopped working after calendar sync was added. The scope now requests each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

The September token response had neither `expires_in` nor `refresh_token`. The server invented a 3600-second lifetime, then cleared the valid token when its refresh job found no refresh token. That caused Rivera's reconnect prompt. The connection now persists until the athlete disconnects or Intervals returns 401; on 401, the server clears the credential and prompts reconnection.

The colleague's note applied to the POST init flow, unique scope areas, the Intervals token exchange fields, and the absence of refresh tokens. The callback still uses signed, time-limited state; it now also checks its purpose and rejects a future timestamp. The account-mismatch guard was added for reconnects. The note's encryption-at-rest advice concerns durable storage: this example stores connections only in memory, so there is no on-disk token store here to encrypt. Its proposed live Intervals verification could not be performed with the placeholder OAuth client in `config.py`; local checks cover syntax and request behavior.
