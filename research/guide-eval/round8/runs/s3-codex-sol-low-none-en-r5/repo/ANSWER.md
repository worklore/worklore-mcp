# Why the nightly review reported nothing

The launchd agent **did run**. The captured `launchctl print` shows six runs and a last exit code of 1. Each run wrote `Not logged in · Please run /login` to `Library/Logs/nightly-review.err`: the headless `claude -p` invocation lacked a usable login, so it could not produce a review.

The script then tried to assign the command's exit code to `status`. In zsh, `status` is a read-only special parameter. That assignment aborted the script before its failure-notification branch, which explains why Telegram received no failure note either. The empty `nightly-review.out` is consistent with the CLI writing the login error to stderr.

I changed the script to use `review_exit_code`, allowing a failed CLI invocation to reach the Telegram failure notification. To make reviews succeed, log the CLI in under the same macOS user account that runs this LaunchAgent and verify that its authentication works from a noninteractive invocation. This snapshot contains no credentials, so that login cannot be repaired here. The job does not need reloading for this script-only change; its next launch will read the updated file.
