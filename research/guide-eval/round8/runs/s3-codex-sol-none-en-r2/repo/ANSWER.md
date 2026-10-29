# Why the nightly review was silent

The agent **was scheduled and ran**. `launchctl-print.txt` shows six runs, a 02:30 calendar trigger, and last exit code 1. The stderr log repeats two lines for each run:

1. `Not logged in · Please run /login` — the `claude -p` process has no usable Claude login in the launchd job's context, so it cannot produce a review.
2. `read-only variable: status` — zsh reserves `status` for the last command's exit code. Assigning to it aborts `nightly-review.zsh` before the failure notification runs. This explains why even the failure note never arrived.

The snapshot now stores Claude's exit code in `claude_exit`, sends a failure note when Claude fails or returns an empty review, and reports notification errors to stderr. The Telegram helper also treats HTTP errors as failures instead of discarding them as apparent success. The Telegram change is preventive; the provided logs do not show a Telegram request being attempted.

**Still needed on the actual Mac:** authenticate the Claude CLI for the `vk` account used by this LaunchAgent (run `claude` interactively and complete `/login`, or configure a valid supported noninteractive credential). The snapshot cannot supply those credentials. After applying these script changes in the actual home directory, run the agent once and inspect `~/Library/Logs/nightly-review.err` if no message arrives. No deployment or external request was made here.
