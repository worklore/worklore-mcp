# Why the nightly review was silent

The agent **did run**: the captured `launchctl print` shows six runs and `last exit code = 1`. Every recorded run failed. `Library/Logs/nightly-review.err` contains six pairs of errors: `Not logged in · Please run /login`, followed by `read-only variable: status` at line 19 of the wrapper.

The launchd environment had `PATH` but no `USER`. In that headless environment, `claude` could not locate its keychain login and exited before producing a review. The wrapper then assigned its exit code to zsh's read-only `status` parameter, which terminated the script before its failure notification. This explains why there was neither a summary nor a failure message. The empty stdout log is consistent with the agent stopping at login.

I added `USER=vk` to the plist, matching the account and paths in the snapshot. The wrapper now saves the agent exit code in `rc`, closes stdin while passing the prompt as an argument, and treats an empty output file as failure. The notifier now makes HTTP error responses from Telegram fail the job instead of hiding them with `curl -sS`.

## Which parts of the colleague's note applied

- **Applied:** inspect `launchctl print` and stderr; the job ran but failed; zsh's `status` assignment killed the failure reporter; setting `USER` addresses the observed headless login failure.
- **Applied as a safeguard:** close stdin with `< /dev/null` because this script passes the prompt as an argument. An empty review now fails instead of sending a success message.
- **Did not apply:** the prompt was already passed as an argument, and the log has no missing-input error. Piping the prompt into `claude -p` is therefore not the fix for this snapshot.

Syntax checks passed for both scripts, and `plutil -lint` accepted the plist. This snapshot cannot prove a live keychain login or Telegram delivery; no launchd job or external service was contacted. After installing these changes in the real home directory, reload the agent and check a run's exit code, output file, and Telegram delivery, including a forced failure.
