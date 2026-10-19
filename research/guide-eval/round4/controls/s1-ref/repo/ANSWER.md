fetch-helper: not safe
repo-stats: not safe as is
cleanup: safe
tone-guide: safe

fetch-helper: scripts/update.sh line 6 runs `curl -fsSL "$HELPER_URL" | sh`. Whatever that URL serves today executes with the user's permissions; nothing is pinned or checked.
repo-stats: scripts/stats.sh runs `npx --yes cloc@latest`, which downloads and executes the latest cloc from npm on every run, unpinned. Pin a version or vendor it.
cleanup: scripts/clean.sh removes and recreates ./build under set -eu; the path is fixed inside the repo. Destructive but bounded.
tone-guide: prose only, no commands or paths.
