# Why the nightly review was silent

The launchd schedule is working. `launchctl-print.txt` shows six runs and the
02:30 calendar trigger. The six repeated entries in
`Library/Logs/nightly-review.err` show that the script ran each time.

Two failures happen in sequence:

1. `claude -p` exits unsuccessfully with `Not logged in · Please run /login`,
   so no review summary is produced. Its output goes to the dated Markdown
   report because the script redirects the command's stdout there.
2. Immediately afterward, the script assigns to `status`, a read-only special
   variable in zsh. That stops the script before it reaches the failure
   notification. The error log records this at line 19 on every run.

I changed the exit-code variable to `agent_exit_code`. A failed agent run can
now reach `notify.sh` and send the failure note; a successful run still sends
the summary. Local stub tests covered both paths without contacting Claude or
Telegram.

To receive review summaries from the real job, authenticate the Claude CLI for
the `vk` account used by this LaunchAgent (or provide its supported
noninteractive credentials there). The snapshot contains no Claude credentials,
so that login cannot be completed here. The script change needs to be copied
to `/Users/vk/bin/nightly-review.zsh`; the plist itself does not need a change.
