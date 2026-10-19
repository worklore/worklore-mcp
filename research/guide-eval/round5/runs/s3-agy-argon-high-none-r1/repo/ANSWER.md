# Why the Nightly Review Job Never Reported Anything

The launchd agent (`gui/501/com.vk.nightly-review`) has been running on schedule every night at 02:30 (`runs = 6`, `last exit code = 1` in `launchctl-print.txt`), but two cascading issues—plus related environment/redirection details—prevented both the review and the failure notification from ever being sent.

---

## 1. Why Not Even a Failure Was Reported: `status` Is Read-Only in `zsh`

In `bin/nightly-review.zsh` (executed by `/bin/zsh`), lines 18–24 were:

```zsh
claude -p "$PROMPT" --output-format text > "$OUT"
status=$?

if [ $status -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $status), see $OUT"
  exit $status
fi
```

In `zsh` (unlike `bash` or `sh`), `status` is a **built-in read-only special parameter** (a synonym for `$?`). Attempting to assign `status=$?` on line 19 triggers a fatal shell error logged in `Library/Logs/nightly-review.err`:

```text
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

When a non-interactive `zsh` script attempts to assign to a read-only variable, `zsh` immediately aborts the script with exit code `1` **before** reaching the `if [ $status -ne 0 ]` failure-reporting block on lines 21–24. Consequently, `bin/notify.sh` was never called.

### Fix
Use a non-reserved variable name (such as `rc=$?`) in `bin/nightly-review.zsh` to store and check `claude`'s exit code.

---

## 2. Why the Review Itself Failed: `claude` Authentication Under `launchd` (`Not logged in · Please run /login`)

Every nightly run logged the following error from `claude` in `Library/Logs/nightly-review.err`:

```text
Not logged in · Please run /login
```

`claude -p` could not find valid credentials when invoked by `launchd` at 02:30 for the following reasons:

1. **Non-login, non-interactive shell and minimal `launchd` environment:**
   - `Library/LaunchAgents/com.vk.nightly-review.plist` ran `/bin/zsh /Users/vk/bin/nightly-review.zsh` without `-l`, and `EnvironmentVariables` only set `PATH` (as confirmed by `launchctl-print.txt`, where `environment` only contains `PATH` and `XPC_SERVICE_NAME`, without `HOME`, `ANTHROPIC_API_KEY`, or `CLAUDE_CODE_OAUTH_TOKEN`).
   - A non-login, non-interactive `zsh` only sources `~/.zshenv`; it never sources `~/.zprofile` or `~/.zshrc`. Any `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` exported in `~/.zprofile` or `~/.zshrc` is missing when run by `launchd`.
2. **Unattended background Keychain access at 02:30 AM / missing OAuth session:**
   - Interactive `claude /login` stores OAuth credentials in the macOS login Keychain (`Claude Code-credentials`) and `~/.claude`.
   - When the job runs unattended at 02:30 AM (when the machine/screen is locked or asleep, or in a background `launchd` context where GUI interaction is disallowed), the login Keychain may be locked or inaccessible (or `claude /login` was not completed / expired), causing `claude` to fail with `Not logged in · Please run /login`.
   - *(Note: `bin/notify.sh` similarly uses `security find-generic-password -s tg-bot -w` when `TG_BOT_TOKEN` is unset, which works when run by hand in an unlocked session, but will also fail at 02:30 AM if the login Keychain is locked on sleep/inactivity unless `TG_BOT_TOKEN` is passed via the environment or the keychain item is accessible.)*

### Fix
- Update `Library/LaunchAgents/com.vk.nightly-review.plist` to invoke `/bin/zsh -l` (login shell) and explicitly set `HOME` (`/Users/vk`) in `EnvironmentVariables`.
- For unattended headless execution at 02:30 AM, provide `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` (and `TG_BOT_TOKEN` if the login Keychain locks during sleep) via `EnvironmentVariables` in the plist or in `~/.zshenv` / `~/.zprofile` (then reload the agent with `launchctl bootout gui/$UID/com.vk.nightly-review` and `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`).

---

## 3. Additional Issues Fixed / Noted

- **Error output missing from `$OUT`:** Line 18 (`claude -p "$PROMPT" --output-format text > "$OUT"`) only redirected `stdout` to `$OUT`, while `stderr` went to `Library/Logs/nightly-review.err`. When `claude` failed, the notification `"nightly review FAILED (exit $rc), see $OUT"` pointed to an empty `$OUT` file. Redirecting `> "$OUT" 2>&1` ensures `$OUT` contains the error message on failure.
- **Headless tool permissions for `claude -p`:** Once authenticated, reviewing commits since `$SINCE` requires `claude` to run read-only `git` commands (`git log`, `git show`, `git diff`). In headless `-p` mode without a TTY, tool permission prompts cannot be answered interactively, so read-only git tools should be pre-approved (via `--allowedTools "Bash(git:*),Read,Grep,Glob"` or in `.claude/settings.json`).
