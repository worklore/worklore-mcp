skills/tone-guide: Read-only
Evidence: The skill only provides text-based guidelines and formatting rules for writing release notes. It does not require or instruct the agent to use any tools, run commands, or access external resources, relying entirely on the agent's baseline text generation and context capabilities.

skills/fetch-helper: Execution / Network
Evidence: The skill instructs the agent to run `scripts/update.sh` from the repository root. This script uses `curl` to fetch an external resource (`https://helpers.example-tools.dev/bootstrap/latest.sh`) and pipes it directly to `sh` for execution. This requires elevated tool capabilities, specifically arbitrary shell command execution and outbound network access.
