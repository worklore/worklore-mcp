skills/fetch-helper: remote-code-execution (network + shell; highest tier)
skills/tone-guide: instructions-only (no code, no tools, no network; lowest tier)

Tier scale used (the repo does not define one), lowest to highest:
instructions-only < runs local code < reads/writes the network < downloads and runs remote code.
Method: read every file statically. Nothing was executed and no URL was fetched.

## skills/fetch-helper — remote-code-execution

- `SKILL.md` step 1 tells the agent to run `scripts/update.sh` from the repo root, so the agent runs shell commands. Steps 2–3 also run `helper --version` and read the script's output.
- `scripts/update.sh` (executable, mode 755):
  - `HELPER_URL="https://helpers.example-tools.dev/bootstrap/latest.sh"`: an external, third-party domain.
  - `curl -fsSL "$HELPER_URL" | sh`: downloads a script and pipes it straight into `sh`. Nothing pins a version or checks a checksum or signature, and the `latest` URL can change at any time. Whatever that server returns runs with the agent's/user's full privileges. What the skill actually does is therefore decided by a remote party, not by the code in this folder, and it can't be reviewed ahead of time.
- Trigger: the description includes "before a release", so the skill can fire on its own during release work, not only when someone explicitly asks for it.
- Recommendation: don't add it as-is. Vendor or pin the bootstrap script (a fixed version plus a sha256 check), or have a human run it.

## skills/tone-guide — instructions-only

- The folder has a single file, `SKILL.md`, with no scripts and no other files.
- The content is writing-style guidance for release notes: lead with the reader impact, one idea per bullet, under 20 words, plain words, describe the user-visible effect, warn about surprises first, never promise dates.
- It contains no commands, no URLs, no file or network access, and no instructions to run tools or override other instructions. All it changes is the wording of drafted text.
- Recommendation: low risk and fine to add.
