# Why nightly-review never reported anything

The job has run 6 times (`runs = 6`, `last exit code = 1`). It fails every time and the failure note never goes out, because of two stacked problems.

1. **`claude -p` is not logged in when launchd runs it.** `Library/Logs/nightly-review.err` repeats `Not logged in · Please run /login`. launchd gives the job a bare environment, so it does not get the login from your interactive shell. The review itself therefore never works.
2. **The failure handler crashes (the reason you got no failure note).** `bin/nightly-review.zsh` ran `status=$?`. In zsh `status` is a read-only special variable, so the script dies with `read-only variable: status` (line 19, also in the `.err` file). It exits with code 1 before it reaches `notify.sh`. Nothing is ever sent, and the cause only shows up in a log file nobody reads.

Smaller issue: `notify.sh` used `curl -sS` without `--fail`. A Telegram HTTP error (bad token or chat id) would have exited 0 and stayed silent.

## Fixed in this folder
- `bin/nightly-review.zsh`: renamed `status` to `rc`, so the failure note is now sent when `claude` fails.
- `bin/notify.sh`: added `--fail` to `curl`, so API errors give a non-zero exit.

## Still for you to do (I can't do it from here)
- Give the job a credential that works without your interactive session. Run `claude setup-token` and add `CLAUDE_CODE_OAUTH_TOKEN` to `EnvironmentVariables` in the plist (or read it from the keychain in the script). Alternatively, run `claude /login` and confirm the login is visible to the `gui/501` launchd domain.
- Reload the agent: `launchctl bootout gui/$UID/com.vk.nightly-review && launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`. Test with `launchctl kickstart -k gui/$UID/com.vk.nightly-review`.
- `notify.sh` reads the bot token from the keychain with `security find-generic-password`. That works by hand, but check that it also works from launchd. A locked keychain or a keychain prompt would make it fail there.
