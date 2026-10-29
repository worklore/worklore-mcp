# Why the nightly job was silent

The job **did run**. The saved `launchctl print` shows six runs and `last exit code = 1`. Its stderr log contains six pairs of errors: `Not logged in · Please run /login`, followed by `read-only variable: status` at line 19.

The plist supplied `PATH` but not `USER`. In this headless launchd environment, `claude` could not find its login and exited before producing a review. The wrapper then assigned to zsh's read-only `status` parameter. That error terminated the script before its failure-notification branch, so neither a summary nor a failure note reached Telegram. The empty stdout log is consistent with this sequence.

I added `USER=vk` to the plist, renamed the exit-code variable to `rc`, and pipe the prompt to `claude -p` through stdin. The wrapper now reports an empty output as a failure and logs elapsed time, so a zero exit code alone cannot mark an empty review as successful. The failure notification runs immediately after either failure check.

From the colleague's note, the following applied: inspect `launchctl print` and stderr first; avoid assigning to zsh `status`; set `USER` for headless CLI login; pass the prompt through stdin; check the actual output and duration rather than relying only on exit code. The note's alternative of passing a prompt argument with closed stdin was not used because this wrapper now pipes the prompt. There is no evidence in this snapshot of a multiline argument parsing failure: the recorded CLI error was specifically a login failure.

Validation in this snapshot: `zsh -n bin/nightly-review.zsh` and plist parsing both passed. A live launchd run and Telegram delivery cannot be verified from this local snapshot; the files have not been deployed or used to contact an external service.
