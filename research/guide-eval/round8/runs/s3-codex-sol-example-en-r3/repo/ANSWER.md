# Why the nightly review was silent

The job **did run**. The saved `launchctl print` shows six runs and `last exit code = 1`. Each run's stderr contains `Not logged in · Please run /login`, followed by `read-only variable: status` at line 19 of the wrapper. The empty stdout log does not mean launchd failed to start it.

There were two stacked causes:

1. `claude` could not use its login in the launchd environment. The saved launchd environment has a `PATH` entry but no `USER`; the wrapper also relies on `HOME`. The exact reason the CLI rejected its login cannot be proven from this snapshot alone, but the missing identity variables are the relevant launchd configuration defect. The plist now supplies `USER=vk` and `HOME=/Users/vk`.
2. After `claude` failed, the wrapper tried `status=$?`. In zsh, `status` is read only. That assignment terminated the script before its failure notification. The wrapper now saves the exit code in `rc` and immediately reports agent failures.

The wrapper now closes the agent's stdin when passing the prompt as a quoted argument, rejects an empty summary, logs run duration and outcome, and treats a failed notification as a job failure. The notifier now fails on HTTP errors and has connection and total timeouts.

## Which parts of the colleague's note applied

- **Applied:** use `launchctl print` and stderr to establish that launchd ran the job; avoid assigning to zsh's `status`; set `USER` for the headless CLI; close stdin when the prompt is an argument; check the actual output and log elapsed time; exercise both notification paths.
- **Did not apply:** this wrapper already passed its multiline prompt as one quoted `-p` argument. The log reports a login error, not “Input must be provided,” so changing to a stdin prompt is not indicated here. The note's particular run count, schedule, and log location are from a different job.

## Verification and limit

The plist passes `plutil -lint`; both scripts pass shell syntax checks. With local stubs, the wrapper produced the expected notification on success, agent failure, empty output, and missing repo. A local `curl` stub confirmed the notifier propagates HTTP-style failures. These checks made no network calls. This is a snapshot, so the loaded agent was not reloaded or kicked off, and live CLI authentication and Telegram delivery remain to be confirmed in the real home directory.
