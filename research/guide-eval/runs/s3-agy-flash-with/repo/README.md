# daybook

Backend of a small public work-journal site. Authors post short entries from anywhere
in the world; every post card shows a date, and the home feed lists posts newest first.

- `journal.py` — `publish(entry, client_tz)` is called by the API handler with the post
  body and the IANA time zone the author's browser reports. `display_date(post, viewer_tz)`
  is what the post card renders. `feed()` is the home feed.

Run tests: `python3 -m unittest discover -s tests`
