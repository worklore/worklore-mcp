# Why the nightly job was silent

The job was running every night. `launchctl-print.txt` shows `runs = 6` and `last exit code = 1`, and the `.err` log has six failures. Two bugs stacked on top of each other.

1. **The agent failed: "Not logged in · Please run /login".** The plist's `EnvironmentVariables` had only `PATH`. Under launchd the `claude` CLI had no `USER`, so it couldn't find its login in the keychain.
   - Fix: added `USER` (and `HOME`) to the plist.
2. **The failure reporter crashed before it could report.** `status=$?` in `nightly-review.zsh` assigns to a read-only zsh variable, which kills the script ("read-only variable: status"). That line sat between the agent call and the `notify.sh` failure call, so no Telegram message was ever sent. The script then exited 1, which is the exit code launchd recorded.
   - Fix: use `rc=$?`.

Hardening, also in the script:
- The agent call now has `< /dev/null`, because the prompt is passed as an argument.
- The script logs the run duration to stderr.
- It treats an empty output file as a failure, so a green exit code with nothing done can't pass as success.
- Duration is included in the Telegram message.

## Colleague's note: what applied
- Applied: check `launchctl print` first; the `status` read-only variable; `USER` in the plist; `< /dev/null`; logging duration; checking the real outcome and not only the exit code.
- Not applicable: the "prompt via stdin" fix. Your prompt arrives fine as an argument, and the log shows a login error, not a missing-prompt error. The 16:50 schedule and the `exit 0` watchdog example also don't apply; your job runs at 02:30.

## Not verified
I couldn't run the job here (no launchd, no `claude`, and no Telegram access in this snapshot). Copy the changed files to your home dir, then `launchctl bootout` and `bootstrap` the plist again. Run `launchctl kickstart -k gui/$UID/com.vk.nightly-review` and check that the exit code is 0, that the output file is fresh, and that the run took a plausible time. Then break the script on purpose once to confirm the failure notification arrives.

Also check that `USER` in the plist matches your actual login name. I used `vk`, taken from the paths in the snapshot.
