# Cache-Control for the ruta-ceramica deploy

## What I changed

Only `scripts/deploy.sh`. Before, it ran a bare `aws s3 sync`, so objects went up
with no `Cache-Control`. Browsers then guessed their own cache lifetime, which is
why returning visitors kept the old `booking.js` for days. The CloudFront
invalidation can't fix that, because it only clears the edge cache, not browser caches.

The script now uploads by file type. Each rule sets the Content-Type and the
Cache-Control together:

| Files                         | Content-Type                            | Cache-Control                       |
|-------------------------------|-----------------------------------------|-------------------------------------|
| `*.html`                      | `text/html; charset=utf-8`              | `public, max-age=300` (5 min)       |
| `*.js` (`booking.js`)         | `application/javascript; charset=utf-8` | `public, max-age=300`               |
| `*.css`                       | `text/css; charset=utf-8`               | `public, max-age=300`               |
| `assets/*.png`, `assets/*.svg`| `image/png`, `image/svg+xml`            | `public, max-age=2592000` (30 days) |

Details:
- **`cp --recursive` instead of `sync` for uploads.** `sync` skips files whose bytes
  haven't changed, so the objects already in the bucket would never get the new
  headers. Now every file is re-uploaded with its headers on every deploy. The site
  is seven files, so this costs almost nothing.
- **Deletions still happen.** After the uploads, `sync --delete --size-only` removes
  objects that are no longer in `src/`. `--size-only` means it won't re-upload
  anything (a re-upload there would go up without the headers).
- **Files with no rule stop the deploy.** If `src/` has a file that no rule covers
  (say a new `.woff2`, or a `.png` outside `assets/`), the script exits before
  uploading anything. That stops a file going up with no header or a guessed type.
  To fix it, add a line to `RULES`.
- **CSS is short-cached** even though you didn't mention it. `styles.css` sits at the
  top level and its name has no version in it, so it has the same stale-file
  problem as `booking.js`.
- **30 days for assets, not a year or `immutable`.** The asset names don't change
  between versions either. If you change `logo.png`, give the new one a new
  filename, or visitors may see the old one for up to 30 days.
- The invalidation stays. It clears the copies cached at the CloudFront edge.

## How I checked it

I didn't deploy or contact AWS. I checked the syntax (`bash -n`), then ran the script
with a fake `aws` command on `PATH` that only prints its arguments. The output showed
the five uploads with the right type and cache header for each, then the
delete-only sync and the invalidation. I also added a dummy `src/x.txt` to test the
"no rule" check: the script stopped with exit 1 before uploading anything.

**After the next real deploy**, check what the server actually sends back. A 200
status alone doesn't prove the headers are right:

```
curl -sI https://<site>/            | grep -iE 'content-type|cache-control'
curl -sI https://<site>/booking.js  | grep -iE 'content-type|cache-control'
curl -sI https://<site>/assets/logo.png | grep -iE 'content-type|cache-control'
```

Expect `text/html` / `application/javascript` / `image/png`, never
`binary/octet-stream`, and the max-age values above. Visitors whose browsers already
hold the old `booking.js` without a header will only pick up the new policy once
their browser's own guessed expiry runs out. From then on, a change reaches visitors
within about 5 minutes.

## Which parts of the colleague's note applied

**Applied:**
- **Set the type and the cache header together, by extension.** This is the core of
  the change. Every upload passes `--content-type` explicitly next to
  `--cache-control`, so the type is never left to chance.
- **Put the fix in the deploy script**, not in a one-off command. Every future
  deploy applies the headers, and nothing has to be run separately.
- **Keep the CloudFront invalidation** after uploading.
- **Verify with `curl -I` and read back `content-type`**, not just the status code.
  That's in the checklist above. I couldn't run it myself without deploying.

**Not applied:**
- **The bucket-to-bucket `cp --metadata-directive REPLACE` approach.** It wasn't
  needed. This script uploads from local `src/` on every deploy, so the headers get
  set at upload time and nothing has to edit objects already in S3. That also avoids
  the trap the note describes: `REPLACE` wiping the content type.
- **The note's TTLs** (86400 for images, CSS bundled with the short group "because
  it's code"). I chose my own values from your "short for HTML and JS, long for
  assets/" and the actual layout. The long cache applies only under `assets/`,
  rather than to any `.png`/`.svg` anywhere.
- **The story about the other S3-compatible host** and the "load in a fresh
  browser" step. Those are general advice, not something to change in this repo.
  The fresh-browser check is still worth doing after the first real deploy.
