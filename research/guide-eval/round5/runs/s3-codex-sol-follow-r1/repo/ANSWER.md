# Why the nightly review was silent

The job **did run**. The saved `launchctl-print.txt` reports `runs = 6` and `last exit code = 1`. `Library/Logs/nightly-review.err` contains six repetitions of the same two errors:

1. `Not logged in · Please run /login`: Claude exited before producing a review. The plist supplied `PATH` but not `USER` in `EnvironmentVariables`. A headless Claude process needs the account name to find its keychain login. The plist now sets `USER` to `vk`.
2. `read-only variable: status`: the zsh wrapper assigned `status=$?` immediately after Claude failed. `status` is a read-only zsh parameter, so the wrapper stopped before its failure notification. The wrapper now uses `rc` and sends the failure notification immediately after checking it.

The original log does **not** show a missing-prompt error. Passing the prompt through stdin is a precaution for the scheduled, headless invocation; it is not an observed cause of these six failures. The wrapper now pipes the prompt to `claude -p`, rejects an empty review even if Claude exits zero, and logs elapsed time to stderr. The notifier now uses `curl -f` so an HTTP error produces a failing exit status.

## Verification

`zsh -n`, `bash -n`, and `plutil -lint` pass. Local runs with stubbed Claude and notifier commands confirmed a success summary, a nonzero Claude failure, a zero-exit empty review, and a missing repository all produce the expected notification and exit code; each logs duration. The success case also confirmed that Claude received the prompt on stdin and wrote a nonempty review.

This directory is a snapshot, so these checks do not prove that the real account is logged into Claude or that Telegram delivers a message. No live launchd job was reloaded or kicked off. After installing these files on the actual Mac, reload the agent, kickstart it, and check `launchctl print gui/$UID/com.vk.nightly-review`, a fresh nonempty review file, the duration in `Library/Logs/nightly-review.err`, and the success notification. Then force one Claude failure and confirm the failure notification.
