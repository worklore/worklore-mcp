# Cause

The note URLs return the static HTML shell with HTTP 200. JavaScript then fetches each note from `/v1/notes/<slug>`. On September 7, `robots.txt` began disallowing all of `/v1/`, including those public GET endpoints. Google could fetch the shell but could not fetch the content it needed to render the note. The app treated every fetch failure as a missing note, so the live inspection rendered “NOT FOUND” under a successful HTTP 200 response. That combination explains the Soft 404 reports. A browser can display the notes because browsers do not apply the crawler's robots.txt restriction to their fetches.

# Fix

`site/robots.txt` now permits the public `/v1/notes` endpoints while continuing to disallow account and authentication routes. `site/app.js` now shows “NOT FOUND” only when the individual note endpoint returns HTTP 404; other request failures show a temporary-unavailability message.

After these files are served, Google must recrawl and rerender the URLs before Search Console can update its status. No external service was contacted or changed here.
