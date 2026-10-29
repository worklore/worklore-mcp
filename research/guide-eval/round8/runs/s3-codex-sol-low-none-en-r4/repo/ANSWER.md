# Why the nightly job was silent

The agent was loaded and did run. `launchctl-print.txt` records six runs and a last exit code of 1. Each run wrote `Not logged in · Please run /login` to `Library/Logs/nightly-review.err`, so the headless `claude -p` process had no usable authentication in launchd's environment. Authentication must be configured for that noninteractive user job before reviews can succeed; an interactive terminal login alone is not evidence that the launchd process has access to it. The snapshot contains no credential to install, and none was added to the repository.

The failure message never reached Telegram because `bin/nightly-review.zsh` assigned `$?` to `status`. In zsh, `status` is a read-only special parameter. That assignment aborted the script before its failure branch, as the repeated line-19 errors in stderr show. It now uses `review_exit` and includes the captured error in the failure notification.

`bin/notify.sh` also discarded Telegram's HTTP response and previously returned success for HTTP errors. It now uses `curl -f`, so HTTP failures produce a nonzero exit and a visible stderr error. This was a reporting blind spot, not a demonstrated cause of these six missing messages; the notifier was never reached on those runs.

To finish setup on the actual Mac, make noninteractive Claude authentication available to the `gui/501` launchd job and verify it with the same user and environment. Keep the credential out of this plist and repository. Then trigger one local run and inspect `Library/Logs/nightly-review.err`, the dated review file, and the Telegram delivery. This snapshot cannot verify the external authentication or delivery.
