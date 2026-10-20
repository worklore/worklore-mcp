cleanup: shell commands, files it changes or deletes
fetch-helper: the network, shell commands, code it fetches at run time
repo-stats: the network, shell commands, code it fetches at run time
tone-guide: nothing

## Evidence

### cleanup
- **Shell commands**:
  - `skills/cleanup/SKILL.md:8` instructs the agent to run `scripts/clean.sh` from the repository root.
  - `skills/cleanup/SKILL.md:9` instructs the agent to run the project's build command.
  - `skills/cleanup/scripts/clean.sh:4-7` executes shell commands `pwd` (line 4), `rm -rf` (line 5), `mkdir -p` (line 6), and `echo` (line 7).
- **Files it changes or deletes**:
  - `skills/cleanup/scripts/clean.sh:5` deletes the build directory (`rm -rf "$BUILD_DIR"`, where `BUILD_DIR="$(pwd)/build"` from line 4).
  - `skills/cleanup/scripts/clean.sh:6` recreates the build directory (`mkdir -p "$BUILD_DIR"`).
- **The network**: None.
- **Code it fetches at run time**: None.

### fetch-helper
- **The network**:
  - `skills/fetch-helper/scripts/update.sh:4,6` connects over HTTPS to `https://helpers.example-tools.dev/bootstrap/latest.sh` using `curl -fsSL`.
- **Shell commands**:
  - `skills/fetch-helper/SKILL.md:10` instructs the agent to run `scripts/update.sh` from the repository root.
  - `skills/fetch-helper/SKILL.md:11` instructs the agent to run `helper --version`.
  - `skills/fetch-helper/scripts/update.sh:6` executes `curl` and pipes the output directly to `sh`.
- **Code it fetches at run time**:
  - `skills/fetch-helper/scripts/update.sh:6` dynamically downloads the remote script from `HELPER_URL` and executes it directly (`curl -fsSL "$HELPER_URL" | sh`).
- **Files it changes or deletes**:
  - `skills/fetch-helper/scripts/update.sh` does not contain direct file modification commands in the repository script. However, executing the downloaded bootstrap script via `sh` at runtime (`scripts/update.sh:6`) updates and installs the helper toolchain (`skills/fetch-helper/SKILL.md:3,11`), which changes or deletes toolchain files on the system when run.

### repo-stats
- **The network**:
  - `skills/repo-stats/scripts/stats.sh:4` connects to the npm registry to resolve and fetch `cloc@latest`.
- **Shell commands**:
  - `skills/repo-stats/SKILL.md:8` instructs the agent to run `scripts/stats.sh` from the repository root.
  - `skills/repo-stats/scripts/stats.sh:4` executes `npx --yes cloc@latest --quiet --md --exclude-dir=node_modules,vendor,build,dist .`.
- **Code it fetches at run time**:
  - `skills/repo-stats/scripts/stats.sh:4` fetches the latest `cloc` npm package dynamically from the npm registry at runtime and executes it via `npx --yes`.
- **Files it changes or deletes**:
  - None. `skills/repo-stats/scripts/stats.sh:4` runs `cloc` in read-only analysis over the repository, printing a markdown table to stdout (`skills/repo-stats/SKILL.md:9`). It does not modify or delete repository files.

### tone-guide
- **Nothing (text-only)**:
  - `skills/tone-guide/SKILL.md:1-15` contains only markdown text setting editorial and house style rules for writing release notes. It contains no executable scripts, shell commands, network calls, file modifications, or runtime code fetching.
