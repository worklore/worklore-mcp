# Root Cause Analysis and Fix

## Why the job never reported anything

Even though `claude` failed with exit code 1 (`Not logged in · Please run /login`), no failure notification was ever delivered to Telegram because of a fatal shell error on line 19 of `bin/nightly-review.zsh`:

```zsh
claude -p "$PROMPT" --output-format text > "$OUT"
status=$?
```

In `zsh`, `status` is a special built-in read-only parameter (an alias for `$?`). Attempting an assignment like `status=$?` causes a fatal execution error:
```
zsh: read-only variable: status
```

Because `status=$?` triggers a fatal error, `zsh` aborts the execution of `bin/nightly-review.zsh` immediately at line 19. The subsequent lines (lines 21–24), which handle non-zero exit codes and call `bin/notify.sh "nightly review FAILED..."`, were never reached.

As recorded in `Library/Logs/nightly-review.err`:
```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

## Fix

In `bin/nightly-review.zsh`, renamed the variable `status` to `exit_code`:
- Changed `status=$?` to `exit_code=$?`
- Updated the check `if [ $exit_code -ne 0 ]; then`
- Updated the notification and exit statements to use `$exit_code`
