# Soft 404 on note pages – Cause and Fix

## Cause

Google Search Console reports **Soft 404** for pages that render correctly in a browser because the crawler cannot fetch the JSON data those pages need. The site’s `robots.txt` contains the rule:

```
User-agent: *
Disallow: /v1/
Disallow: /admin/
```

All page content is populated client‑side via JavaScript that calls the internal API under the `/v1/` path. When Googlebot renders the page it respects `robots.txt`, so the request to `/v1/...` is blocked. The fetch fails, the client‑side code falls back to a *"Not found"* UI (HTTP 200 with a “page not found” message). Google interprets a successful HTTP 200 that displays a “not‑found” message as a **soft 404**.

## Fix

1. **Allow the public read endpoints** that the pages need while keeping the rest of the API blocked.
   ```
   User-agent: *
   Allow: /v1/stories        # public read endpoint needed by pages
   Disallow: /v1/            # keep everything else blocked (POST‑only, admin, etc.)
   Disallow: /admin/
   ```
   - The longest‑match rule wins, so `Allow: /v1/stories` overrides the broader `Disallow: /v1/` for the allowed path.
2. **Keep more specific disallow rules** for endpoints that must stay hidden, e.g.:
   ```
   Disallow: /v1/stories/*/reproduced   # still blocked
   ```
3. **Verify the rules** locally before deploying:
   ```bash
   # Use a script that mimics Google’s longest‑match algorithm (not python’s robotparser)
   curl -s https://<site>/robots.txt
   # Test each affected URL with curl – you should get the full page content, not the "not found" UI.
   ```
4. **Deploy the updated `robots.txt`** and request a recrawl in Search Console (Settings → Crawling → robots.txt → Request recrawl).
5. After Google re‑crawls, the pages will move from *Soft 404* to *Crawled – currently not indexed* and eventually to *Indexed*.

---

**Summary**: The soft 404 reports are caused by `robots.txt` blocking the API calls needed for client‑side rendering. Updating `robots.txt` to allow those read endpoints resolves the issue.
