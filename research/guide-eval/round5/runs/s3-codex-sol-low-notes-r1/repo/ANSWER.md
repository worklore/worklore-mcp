# Why the nightly job was silent

`launchctl-print.txt` shows the agent did run six times and last exited with code 1. Its stderr log records `Not logged in · Please run /login` on every run. The launchd environment lacked `USER`, which the headless `claude` CLI needs to find its saved login. The plist now sets `USER=vk`.

After `claude` failed, the script tried `status=$?`. `status` is read-only in zsh, so that assignment terminated the script before it could send the failure notification. The script now captures the exit code in `rc` and sends a failure note when it is nonzero.

The prompt now goes through stdin to `claude -p`, following the local troubleshooting note for unattended runs. This avoids relying on a multiline prompt argument in that context.

The stdout log is empty because the review output is redirected to a dated Markdown file, while the errors went to `nightly-review.err`. No Telegram delivery can be verified from this snapshot; the live job must be reloaded with the edited plist before its environment changes take effect.
