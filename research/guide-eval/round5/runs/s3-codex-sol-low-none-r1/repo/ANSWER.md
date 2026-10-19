# Why the nightly review was silent

The agent **is running**: the captured `launchctl print` shows six runs and a last exit code of 1. The plist's calendar trigger, program path, and log paths are present.

Each captured run failed in two steps:

1. `claude -p` printed `Not logged in · Please run /login`. The account used by this launchd job has no usable Claude CLI login, so it cannot produce a review until that login is set up for unattended use.
2. The script then assigned `$?` to `status`. In zsh, `status` is a read-only special parameter. The assignment raised `read-only variable: status` and terminated the script before its failure-notification branch. This explains why even the failed runs sent no Telegram message.

I changed the script to save the exit code in `review_exit` and capture CLI errors in the dated output file. Failed runs now attempt a Telegram failure message with the exit code and a short error excerpt. The Claude login still needs to be configured in the real home directory; this snapshot cannot authenticate it. The notifier's keychain access from launchd is not established by the supplied logs, so confirm delivery on the next run.
