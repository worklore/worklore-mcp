# Why Search Console reports Soft 404

The note URL itself is crawlable and returns HTTP 200, but the HTML is a shell. `site/app.js` fetches `/v1/notes/<slug>` before it can show a note. `site/robots.txt` blocked all of `/v1/`, so Google's renderer could not fetch that data. The app treats any failed fetch as a missing note and displays “NOT FOUND — No note lives at this address” while the page still has HTTP 200. The October 16 URL Inspection export shows exactly that rendered text and a Soft 404 verdict for `/n/drip-line-pressure`. Four recently crawled notes have the same verdict. The robots rule was added September 7; the two listed notes last crawled in August remain indexed. This strongly supports the blocked API request as the cause, though the export does not include a network log of Google's API request.

# Fix

Updated `site/robots.txt` to allow the public `/v1/notes` list and note detail endpoints while keeping the general `/v1/` block. A more specific rule blocks `/v1/notes/*/reactions`; `/v1/me`, `/v1/auth/token`, and `/admin/` remain blocked. Robots rules cannot distinguish GET from POST on the same `/v1/notes` path, so the existing bearer authentication continues to protect note creation and edits.

Locally checked the rules using longest matching rule precedence: `/v1/notes?limit=50` and `/v1/notes/drip-line-pressure` are allowed; reactions, user, auth, and admin paths are blocked. The note page URL remains allowed. The changed file has not been deployed, so Search Console's live result and later indexing status cannot yet be verified here.

# How the colleague's note applies

The same mechanism applies: a JavaScript rendered page needs a same-domain API that robots.txt blocked, and an API failure becomes a “not found” screen served with HTTP 200. The suggested narrow allow rule, longer reaction rule, and longest-match check apply here. Its discovery advice is separate: this site's initial HTML also lacks note links, but that does not explain a URL that Google already crawled and rendered as “NOT FOUND.” Its recrawl and indexing timeline describes a different site and is not evidence of this fix's outcome.
