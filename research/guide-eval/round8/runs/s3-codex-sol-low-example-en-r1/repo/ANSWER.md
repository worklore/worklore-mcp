# Why the nightly review was silent

The job **did run**. The saved `launchctl-print.txt` shows six runs and `last exit code = 1`; the empty stdout file alone was misleading. Each run's stderr says `Not logged in · Please run /login`, followed by `read-only variable: status` at line 19 of the wrapper.

Two failures combined:

1. The launchd environment in the snapshot omitted `USER`. The headless `claude` invocation failed to find its login. I added `USER=vk` to the plist's `EnvironmentVariables`.
2. Immediately after `claude`, the zsh script assigned `status=$?`. `status` is a read-only zsh parameter, so the script stopped before its failure notification. I changed it to `rc=$?` and use that value for the notification and exit code.

I also closed the prompt-as-argument invocation's stdin with `< /dev/null`, and made an empty output file a reported failure rather than a success message. These guard against silent or false-success runs; the captured log does not show either as the cause of the six failures.

## Colleague's note

Applicable: inspect `launchctl print` and stderr; avoid zsh's read-only `status`; set `USER` for the headless CLI; close stdin when passing the prompt as an argument; check the real output as well as the exit code.

Not evidenced here: a missing prompt. This script already passes the prompt as the `-p` argument, and the recorded error is a login error. Piping the prompt via stdin is therefore unnecessary. There is no captured evidence of a timeout or an implausibly short run, and the snapshot contains no live launchd domain to kickstart.

## Verification

`zsh -n bin/nightly-review.zsh`, `plutil -lint Library/LaunchAgents/com.vk.nightly-review.plist`, and `git diff --check` pass. Live confirmation requires installing these changed files in the real home directory, reloading the agent, and checking that a fresh summary file and Telegram message appear; this snapshot was not deployed or sent to Telegram.
