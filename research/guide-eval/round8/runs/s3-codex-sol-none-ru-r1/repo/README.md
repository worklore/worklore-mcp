# nightly-review (snapshot of my home dir, the relevant bits)

A launchd user agent runs `bin/nightly-review.zsh` every night at 02:30. The
script asks a headless coding agent to review yesterday's commits in
~/projects/shop and sends me the summary (or a failure note) over Telegram
via `bin/notify.sh`.

Layout, relative to my home:

- `Library/LaunchAgents/com.vk.nightly-review.plist` — loaded with
  `launchctl bootstrap gui/$UID ...` on 2026-10-12
- `bin/nightly-review.zsh` — the job
- `bin/notify.sh` — Telegram notifier (works when run by hand)
- `Library/Logs/` — where the plist points stdout/stderr
- `launchctl-print.txt` — output of `launchctl print gui/501/com.vk.nightly-review`, captured 2026-10-18 09:10

I have received nothing on Telegram since it was loaded: no summaries, no
failure notes.
