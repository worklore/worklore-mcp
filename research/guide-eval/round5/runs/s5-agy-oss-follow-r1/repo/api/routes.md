# API routes (all under /v1/, same domain as the site)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | /v1/notes | none | list public notes (`?limit=`) |
| GET | /v1/notes/{slug} | none | one public note (JSON with `html`) |
| POST | /v1/notes | bearer | create a note |
| PUT | /v1/notes/{slug} | bearer | edit a note |
| POST | /v1/notes/{slug}/reactions | bearer | react (per user) |
| GET | /v1/me | bearer | the signed-in user |
| GET | /v1/me/drafts | bearer | the user's drafts |
| POST | /v1/auth/token | none | sign-in exchange |

Unauthenticated POST/PUT return 401. Crawlers hitting POST-only paths with GET
were logging 404s and 405s all September, which is why `/v1/` was added to
robots.txt on 2026-09-07.
