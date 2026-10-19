# fieldnotes.example — site + API

- `site/` — the static front end (S3 + CloudFront, same domain). Every page is
  one HTML shell; `app.js` fetches the content from the API and renders it.
- `api/` — the API (Lambda behind the same CloudFront distribution, under `/v1/`).
  `api/routes.md` lists the routes.
- `search-console/` — exports from Google Search Console, 2026-10-16.

Pages are at `/n/<slug>` (CloudFront rewrites `/n/*` to `/index.html`).
Sitemap lists all 58 note pages.
