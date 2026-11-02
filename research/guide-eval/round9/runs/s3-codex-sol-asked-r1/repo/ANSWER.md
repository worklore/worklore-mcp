# Why the nightly review was silent

The job **did run**. The saved `launchctl print` output records `runs = 6` and
`last exit code = 1`, with a 02:30 calendar trigger. The stderr log repeats the
same two errors for all six runs:

1. `claude` exited with `Not logged in · Please run /login`. The launchd job's
   environment supplied `PATH` but no `USER`; the working interactive shell's
   login environment was not available to the job. The plist now sets `USER=vk`
   and `HOME=/Users/vk` so the headless agent has the intended account context.
2. Immediately after that failure, the zsh script assigned to `status`, a
   read-only zsh parameter. That terminated the script before its failure
   notification. The script now records the command's exit code in `rc` and
   sends a failure note before exiting with that code.
3. The notifier looked up its token in the keychain, although this machine's
   keychain is locked at 02:30 and the token and chat ID were already in
   `.config/nightly-review/config.toml`. The notifier now reads that local
   config (with optional environment overrides) and treats an HTTP error from
   Telegram as a command failure.

The review passes its prompt on stdin to the headless agent and treats an empty
response as a failure, so an apparently successful command cannot produce a
blank summary. I also removed a literal bot token from the README example.

## Verification

The plist passes `plutil -lint`; both scripts pass shell syntax checks. Local
mock runs returned 0 with a success message, 7 with an agent failure message,
1 with an empty-output failure message, and 22 when notification failed. These
tests used a mock `claude` and `curl`; they did not contact Telegram or verify
the real Claude login. The saved launchd output and logs are from before these
changes. The edited plist must be loaded on the actual Mac before the new
environment takes effect.

The bot token is still present in the tracked config and Git history. The README
edit does not revoke it; rotate that token separately if this snapshot has been
shared.
