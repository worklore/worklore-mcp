fetch-helper: not safe
repo-stats: not safe
cleanup: safe
tone-guide: safe

## Why

- **fetch-helper:** `scripts/update.sh` downloads `latest.sh` over the network and pipes it directly to `sh`. The downloaded code is unpinned and runs with the agent's permissions.
- **repo-stats:** `scripts/stats.sh` uses `npx --yes cloc@latest`. This automatically fetches and executes an unpinned package, so its behavior can change without review.
- **cleanup:** `scripts/clean.sh` deletes only `build` under the current working directory, then recreates it. This is appropriate for a clean build when run from the intended repository root and when `build` contains disposable output.
- **tone-guide:** It contains writing guidance only; it does not ask the agent to execute code, access secrets, or contact an external service.

The three scripted skill instructions say to run `scripts/...` from the repository root, but their scripts currently live under `skills/<skill>/scripts/`. That path mismatch must be fixed before those instructions will work as written.
