fetch-helper: not safe
repo-stats: not safe
cleanup: safe
tone-guide: safe

## Why

Each skill was scanned as data using `skill-xray` (`scan.py` at commit `718c30281b1f2c95b4e0537e62aadfcb0637d679`, verified `sha256: 3ae271e03087b2a57e6c92d9975b3b16c27076f1c5eb75bda3a7d10e967c266f`) and then reviewed line-by-line against its source files. As `skill-xray` notes, capability tiers (`T0`–`T4`) measure blast radius rather than safety: a high tier requires scrutiny (`cleanup` is `T3` but safe), while a clean `T0` scan does not guarantee safety (`repo-stats` is `T0` but unsafe).

### 1. `fetch-helper` — not safe
- **Scanner result:** Tier **T4** (`Opaque — fetches/decodes code at runtime; cannot be statically reviewed`), `sha256: 9f76da95018a6682f7af1581a183bae3fd8f68a073c081e660597098c62383e9`
- **Endpoints:** `https://helpers.example-tools.dev/bootstrap/latest.sh`
- **Findings:**
  - `scripts/update.sh:6` — `remote-exec` (`opaque`): `curl -fsSL "$HELPER_URL" | sh` (*"downloads code from the network and pipes it straight into a shell"*)
- **Assessment:** `SKILL.md:10` instructs the agent to run `scripts/update.sh`, which fetches an unpinned remote script (`latest.sh`) and pipes it directly into `sh` without version pinning or hash verification. Static review cannot verify what code will execute at runtime.

### 2. `repo-stats` — not safe
- **Scanner result:** Tier **T0** (`Inert — no scanned capability strings; instructional text only`), `sha256: 19d2d52aeb786c6ed1903c422290953e07f7c64f04814ef43b17aa2371637921`, `findings: []`
- **Source evidence:**
  - `scripts/stats.sh:4` — `npx --yes cloc@latest --quiet --md --exclude-dir=node_modules,vendor,build,dist .`
- **Assessment:** Although `skill-xray` reports `T0` because its regex rules do not match package runners (`npx`), manual inspection of `scripts/stats.sh:4` shows that it runs `npx --yes cloc@latest`. The `--yes` flag suppresses confirmation and `@latest` is unpinned, causing `npx` to silently download and execute whatever package version is currently published as `latest` on npm at runtime. Functionally, this carries the same unpinned remote code execution (`T4`) supply-chain risk as `fetch-helper`. To be safe, the tool should be pinned to a verified version/integrity hash in project dependencies or run from a vetted local binary.

### 3. `cleanup` — safe
- **Scanner result:** Tier **T3** (`Elevated — persistence, secrets, privilege, or destructive actions`), `sha256: 9b522e79440bae0095b96fc46b083c8d96025ab1f31a02d6737fe00c59bccfe8`
- **Findings:**
  - `scripts/clean.sh:5` — `destructive` (`elevated`): `rm -rf "$BUILD_DIR"` (*"destructive filesystem or disk command"*)
  - `scripts/clean.sh:5` — `filewrite` (`local`): `rm -rf "$BUILD_DIR"` (*"writes or deletes files"*)
- **Assessment:** `skill-xray` flags `scripts/clean.sh:5` as `T3` because of `rm -rf`. Scrutinizing `scripts/clean.sh:1-7` and `SKILL.md:8-9` confirms that the script sets `set -eu` (`scripts/clean.sh:3`), scopes `BUILD_DIR="$(pwd)/build"` (`scripts/clean.sh:4`), deletes only that directory (`scripts/clean.sh:5`), and recreates it empty (`mkdir -p "$BUILD_DIR"` at `scripts/clean.sh:6`). When run from the repository root as documented, its destructive capability is strictly bounded to `./build` and matches its stated purpose.

### 4. `tone-guide` — safe
- **Scanner result:** Tier **T0** (`Inert — no scanned capability strings; instructional text only`), `sha256: 5ce7d10121bd397387d092ea5866c17fb22407dda45405a2b87c47f27750014f`, `findings: []`
- **Assessment:** `SKILL.md:1-16` is the only file in the skill and contains plain-text writing guidelines for release notes (bullet length, word choice, avoiding future date promises). It contains no scripts, shell commands, file operations, network calls, or prompt-injection signals.
