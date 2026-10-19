# Why the nightly job was silent

The job **did run**. The saved `launchctl print` shows `runs = 6` and `last exit code = 1`, and `Library/Logs/nightly-review.err` has six pairs of errors. The first error in each pair is `Not logged in · Please run /login` from `claude`. The plist provided `PATH` but no `USER`; the missing login identity is the supported explanation for that headless authentication failure. The snapshot cannot prove a successful authenticated run, so this part still needs checking on the real Mac after the updated plist is loaded.

The second error explains why no failure message arrived: `bin/nightly-review.zsh` assigned `status=$?` immediately after `claude`. In zsh, `status` is read only. The assignment terminated the script before its Telegram failure branch. The empty stdout log does not mean launchd never started the job; the review output was redirected to a dated Markdown file.

## Fixes in this snapshot

- Added `USER=vk` to the LaunchAgent environment for the headless CLI's login lookup.
- Replaced the read only `status` assignment with a conditional that captures the agent exit code in `rc` and sends the failure notification. It also reports an empty summary as a failure and logs elapsed time.
- Kept the existing prompt argument and closed stdin with `< /dev/null`, so the CLI cannot wait for input after receiving that argument.
- Made the notifier report a failed keychain lookup or HTTP response to stderr instead of silently accepting it. This is a safeguard; neither failure is shown in the saved log.

## What applied from the colleague's note

The `launchctl print` and stderr checks, zsh's read only `status`, the missing `USER` in the plist, closed stdin for an argument prompt, duration logging, and testing the failure path all applied. The note's **missing prompt** diagnosis did not: this script already supplied `"$PROMPT"` as a single quoted argument, and the saved error is about login. Piping the prompt through stdin would be an alternative, but there is no evidence it is needed here. The note's correction about exit codes also applies: six runs and exit code 1 establish attempted runs and failure, not a completed review.

## Verification and deployment limit

Syntax checks passed for both shell scripts, and `plutil -lint` accepted the plist. With local mock `claude` and notifier commands, the job produced a success notification on a nonempty summary, a failure notification and exit code 7 when the agent failed, and a failure notification and exit code 1 on empty output. Mocked keychain and HTTP failures also made the notifier exit nonzero. No live `claude`, Telegram, or launchd invocation was made.

These edits are only in the provided snapshot. On the real Mac, the updated plist must be loaded before `USER` takes effect. Then verify a run with `launchctl print gui/$UID/com.vk.nightly-review`, the fresh dated summary, elapsed time in stderr, and receipt of the success notification. A forced local agent failure should also produce a Telegram failure notification. A fresh `Not logged in` error after loading the plist would require checking the CLI's login and keychain access in that launchd context.
