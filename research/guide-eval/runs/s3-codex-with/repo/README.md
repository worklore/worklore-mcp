# daybook

Backend of a small public work-journal site. Authors post short entries from anywhere
in the world; every post card shows a date, and the home feed lists posts newest first.

- `journal.py` — `publish(entry, client_tz)` is called by the API handler. `entry`
  must include `date` as `YYYY-MM-DD`, captured from the author's device in its local
  calendar at write time (for example, `date +%F` on a command line). The backend
  stores this value unchanged; it never derives it from the server clock or converts
  it for viewers. `client_tz` is the browser's IANA time zone and is kept on the post.
  Each submission also gets a server-side UTC `received_at` timestamp for feed order.
  `display_date(post, viewer_tz)` returns the author's date as written, and `feed()`
  lists posts by `received_at` newest first, falling back to `date` for older posts.

Run tests: `python3 -m unittest discover -s tests`
