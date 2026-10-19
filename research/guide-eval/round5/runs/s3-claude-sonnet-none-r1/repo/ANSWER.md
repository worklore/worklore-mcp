# Why the nightly job never reported anything

1. **`claude` is not logged in in the launchd context.** Every run in
   `nightly-review.err` says `Not logged in · Please run /login`, so the review
   itself fails every night (`last exit code = 1`, `runs = 6`). Interactive
   login state is not available to the launchd job. This one I could not fix
   from here: run `claude setup-token` and provide the token to the job
   (e.g. `CLAUDE_CODE_OAUTH_TOKEN` in the plist's `EnvironmentVariables`, or
   read it from the keychain in the script), then reload the agent.

2. **The failure handler crashed, so no failure note was ever sent.** The
   script did `status=$?`, but `status` is a read-only special variable in zsh
   (`read-only variable: status`, err line 2 of each run). The script aborted
   before reaching the `notify.sh` call. Fixed: renamed to `rc`.

3. **The failure message pointed at an empty file and hid the real error.**
   stderr went to launchd's log, while `$OUT` was empty. Now stderr is saved
   to `nightly-review-DATE.err` and its first 200 bytes go into the note.

4. **`notify.sh` could fail silently.** `curl -sS` exits 0 on Telegram HTTP
   errors (bad token/chat) and output goes to /dev/null. Changed to
   `--fail-with-body` so a rejected message produces a non-zero exit and an
   error on stderr (visible in `nightly-review.err`).

Note: the plist's PATH (`/opt/homebrew/bin:...`) is fine if `claude` lives
there; if it is installed elsewhere (e.g. `~/.local/bin`), add that dir to the
plist PATH too. After editing, reload with `launchctl bootout` / `bootstrap`.
