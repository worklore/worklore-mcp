---

# Collecting leads from a static site with Apps Script and a honeypot

I keep a small site for our family kennel. It is a static page: no server, no
database, no build step.

This year's litter sold out in August and the next one is a year or more away,
so the site had nothing left to sell while people kept arriving from search and
from Instagram and asking anyway. I wanted a waiting list.

The reflex at that point is to reach for infrastructure. An AWS account with a
Lambda and a table behind it. A Supabase project. A form service with a monthly
bill. I have used all three, and each one is a thing you then own: credentials
to rotate, a free tier that quietly changes, a dashboard to log into a year
later when you have forgotten how you wired it. For a kennel that produces a
litter every two years, that is not engineering. It is a subscription to future
confusion.

The answer was a spreadsheet, and I already had one. Google Apps Script turns
it into an endpoint: Extensions, Apps Script, about twenty lines with a
`doPost`, deploy it as a web app, and the sheet accepts POSTs, appends rows and
emails me. Nothing to create, nothing to pay, no credentials in the page. The
data and the endpoint live in the same place, which is what I actually care
about in eighteen months when someone from that list writes back.

Two practical notes. A hidden field catches bots without a captcha. And the
browser will not POST JSON to Apps Script directly, because it never answers the
CORS preflight; sending it as `text/plain` with `no-cors` makes it a simple
request and it goes through, at the cost of an opaque response. The sheet and
the email are the confirmation, not the fetch.

Simple things should stay simple.

## Reproduce this

Prerequisites: a static site you can edit and deploy, and a Google account.

Your agent will need from you: which spreadsheet to write into (or permission
to create one), the address to notify, and the list of fields to collect.

Steps:

1. Create a Google Sheet for submissions. Its ID is the long string in the URL
   between `/d/` and `/edit`.
2. In that sheet choose Extensions, then Apps Script. Write a `doPost(e)` that
   parses `e.postData.contents` as JSON; returns success immediately and writes
   nothing if the honeypot field is non-empty; rejects missing required fields;
   takes a `LockService.getScriptLock()` before writing so two submissions in
   the same second cannot interleave; appends a row via
   `SpreadsheetApp.openById(<id>).getSheets()[0].appendRow([...])` with a
   timestamp first; releases the lock; then sends a notification with
   `MailApp.sendEmail`. Truncate every field to a maximum length before writing.
3. Deploy, New deployment, type "Web app", Execute as **Me**, Who has access
   **Anyone**. Authorise it. Copy the URL ending in `/exec`.
4. In the page, add the form with the real fields, plus a hidden input that no
   human can see or tab into (`tabindex="-1"`, `aria-hidden="true"`) as the
   honeypot, and a status element with `role="status"` and `aria-live="polite"`.
5. Validate in the browser first, setting `aria-invalid` on each field and
   focusing the first bad one, so a screen reader announces the problem.
6. Submit with `fetch(url, { method: "POST", mode: "no-cors", headers: {
   "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(data) })`.
   Do not use `application/json`: it triggers a preflight that Apps Script
   never answers. Because the response is opaque, treat the resolved promise as
   success and let the sheet and the email be the source of truth.
7. Read `utm_source`, `utm_medium`, `utm_campaign` from the query string, fall
   back to `document.referrer`, and send that as a `source` field.
8. When you later change the script, use Deploy, Manage deployments, the pencil
   icon, and set Version to "New version". A fresh deployment would give you a
   different `/exec` URL and silently break the live form.

Verify: submit the form on the deployed site. A row appears in the sheet within
a few seconds and the notification email arrives. Then fill the honeypot field
from devtools and submit again: no new row appears, and the endpoint still
reports success, so a bot sees nothing unusual.
