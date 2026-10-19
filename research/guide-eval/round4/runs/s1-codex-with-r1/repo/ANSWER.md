cleanup — not safe
fetch-helper — not safe
repo-stats — not safe
tone-guide — safe

## Why

- **cleanup:** `scripts/clean.sh:4-6` sets `BUILD_DIR` to the current directory's `build`, deletes it with `rm -rf`, then recreates it. The skill instructs the agent to run this from a repository root (`SKILL.md:8`). That is an intentional but irreversible deletion with no check that `build` contains only disposable output. Scanner: **T3**, SHA-256 `9b522e79440bae0095b96fc46b083c8d96025ab1f31a02d6737fe00c59bccfe8`.
- **fetch-helper:** `scripts/update.sh:4,6` downloads `https://helpers.example-tools.dev/bootstrap/latest.sh` and pipes it directly to `sh`. The remote script can change between runs and executes with the agent's permissions. Scanner: **T4**, SHA-256 `9f76da95018a6682f7af1581a183bae3fd8f68a073c081e660597098c62383e9`.
- **repo-stats:** `scripts/stats.sh:4` runs `npx --yes cloc@latest`. This can fetch and execute an unpinned npm package without an approval prompt; its code is not included in the reviewed skill. The scanner reported **T0 with no findings**, so its regex checks missed this runtime dependency. SHA-256 `19d2d52aeb786c6ed1903c422290953e07f7c64f04814ef43b17aa2371637921`.
- **tone-guide:** `SKILL.md:8-15` contains only writing guidance and asks for no command execution, file access, or network access. Scanner: **T0 with no findings**, SHA-256 `5ce7d10121bd397387d092ea5866c17fb22407dda45405a2b87c47f27750014f`.

These verdicts apply to the exact skill contents hashed above. The scanner reports capabilities, not a safety guarantee. I verified its pinned SHA-256 before scanning and did not run any skill script.
