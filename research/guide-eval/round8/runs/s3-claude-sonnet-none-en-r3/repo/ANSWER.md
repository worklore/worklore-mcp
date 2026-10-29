# Why nightly-review never reports anything

1. **The job itself can't run `claude`: "Not logged in · Please run /login"** (every run in `nightly-review.err`).
   The launchd agent has no access to the interactive login session, so headless `claude -p` has no credentials.
   Fix (needs you, I can't do it here): run `claude setup-token` once and give the job the token, e.g.
   `CLAUDE_CODE_OAUTH_TOKEN` in the plist's `EnvironmentVariables` (or read it from the keychain in the script),
   then `launchctl bootout` / `bootstrap` the agent again.

2. **The failure handler crashes before it can notify.** `status=$?` in zsh assigns to the read-only special
   variable `status`, which aborts the script (`read-only variable: status`, line 19, exit 1). So the
   "FAILED" Telegram message was never sent. Fixed by renaming the variable to `rc`.

3. **Notifier hardening (secondary).** `notify.sh` used `curl -sS` with output discarded, so Telegram HTTP errors
   (bad token/chat) exited 0 silently. Added `-f`. The scripts now log "notify failed" to stderr if notifying fails.
   Also note `security find-generic-password` can fail from launchd if the keychain is locked;
   if the err log shows that after fixing 1–2, set `TG_BOT_TOKEN` in the plist environment instead.

Not a cause: schedule and paths are fine (`runs = 6`, `last exit code = 1` in launchctl-print.txt); PATH is OK as `claude` was found.
