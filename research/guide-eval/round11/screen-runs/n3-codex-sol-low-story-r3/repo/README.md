# fieldnotes

A static site for short field notes. The site itself is plain files in `site/`
(the shell page, styles, script, robots.txt). Every note and every author also
gets a prerendered page, so it can be shared and indexed: `build_pages.py`
reads `content/stories.json` and writes `.build/pages/s/<slug>` and
`.build/pages/a/<handle>`. Private notes get no page.

The site is served from an S3 bucket behind CloudFront. `deploy.sh` builds the
pages, syncs `site/` to the bucket and uploads the pages. The page keys have no
file extension (`s/<slug>`, not `s/<slug>.html`), so S3 cannot guess their
type: each one is uploaded with `--content-type "text/html; charset=utf-8"`,
otherwise browsers download the page instead of showing it.

CI runs `./deploy.sh` on every push to main with `BUCKET` set and its own AWS
credentials. There is no test bucket.
