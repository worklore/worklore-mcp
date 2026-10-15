skills/fetch-helper: High capability — remote code execution
Evidence: `SKILL.md` instructs the agent to run `scripts/update.sh`. That script uses `curl -fsSL "$HELPER_URL" | sh` to download and execute code from `https://helpers.example-tools.dev/bootstrap/latest.sh`. The downloaded code can change independently of this folder and would run with the agent's shell permissions.

skills/tone-guide: Low capability — instructions only
Evidence: `SKILL.md` contains only wording and formatting guidance for release notes. The folder has no script or instruction to run a command, access a network service, or modify files beyond the requested writing task.
