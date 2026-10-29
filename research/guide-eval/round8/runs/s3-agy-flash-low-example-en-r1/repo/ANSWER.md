# Root Causes and Fixes

## 1. Causes of the Silence

Examination of `Library/Logs/nightly-review.err` revealed the two stacked causes that led to complete silence:

1. **Missing `USER` environment variable in launchd execution context:**
   - In `Library/Logs/nightly-review.err`, every run produced:
     ```
     Not logged in · Please run /login
     ```
   - Launchd executes jobs in a minimal environment. Without `USER` defined under `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`, the CLI (`claude`) cannot access the user's login session / keychain credentials, resulting in an immediate failure with exit code 1.

2. **Assignment to read-only variable `status` in zsh:**
   - In `bin/nightly-review.zsh` line 19, the script executed:
     ```zsh
     status=$?
     ```
   - In zsh, `status` is a special read-only built-in variable (an alias for `$?`). Attempting to assign to `status` causes zsh to throw a fatal error:
     ```
     /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
     ```
   - This fatal error immediately aborted the script before it could reach the error-handling block and execute `bin/notify.sh`. Hence, no failure notification was ever dispatched.

3. **Potential stdin hanging when passing prompt as an argument:**
   - When running `claude -p "$PROMPT"` under launchd without an explicit stdin redirection, CLI tools expecting potential stdin input can hang or exhibit undefined behavior. Closing stdin (`< /dev/null`) prevents this issue.

---

## 2. Colleagues Note Analysis: What Applied vs What Was Ignored

From the colleague's note:

- **Applied:**
  - **Read-only `status` variable in zsh:** Directly matched line 19 in `bin/nightly-review.zsh` and the error logged in `nightly-review.err`. Replaced `status=$?` with `rc=$?`.
  - **Missing `USER` in plist `EnvironmentVariables`:** Directly matched the `Not logged in · Please run /login` error in `nightly-review.err`. Added `<key>USER</key><string>vk</string>` to the plist.
  - **Redirecting stdin (`< /dev/null`) with `-p` argument:** Applied `< /dev/null` to `claude -p "$PROMPT"` to avoid any launchd stdin hang traps.

- **Ignored / Not Applicable:**
  - **"Input must be provided either through stdin or as a prompt argument" / prompt piping:** In this script, the prompt was already provided via the `-p "$PROMPT"` argument rather than failing due to missing prompt arguments.
  - **Verification steps involving live launchd commands (`launchctl print`, `launchctl kickstart`):** Since this repository is a directory snapshot of the user's home files and external service interaction is restricted per ground rules, live launchctl reload / daemon kickstart commands were not executed on the host system.

---

## 3. Fixes Implemented

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - Added `USER` key set to `vk` under `EnvironmentVariables`.

2. **`bin/nightly-review.zsh`**:
   - Replaced assignment to read-only `status` with `rc=$?` (and updated variable references in the failure notification block).
   - Added `< /dev/null` to `claude -p "$PROMPT" ...` to ensure stdin is safely closed.
