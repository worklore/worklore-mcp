skills/fetch-helper: T4
skills/tone-guide: T0

## Evidence

### skills/fetch-helper: T4 (Opaque)
- **Classification**: T4 (Opaque — fetches/decodes code at runtime; cannot be statically reviewed)
- **Artifact SHA-256**: `9f76da95018a6682f7af1581a183bae3fd8f68a073c081e660597098c62383e9`
- **Endpoints detected**: `https://helpers.example-tools.dev/bootstrap/latest.sh`
- **Findings**:
  - `skills/fetch-helper/scripts/update.sh:6`: Category `remote-exec` (severity: `opaque`)
    - Code: `curl -fsSL "$HELPER_URL" | sh`
    - Why: Downloads code from the network (`https://helpers.example-tools.dev/bootstrap/latest.sh`) and pipes it straight into a shell (`sh`), making static review impossible.
  - `skills/fetch-helper/SKILL.md:10`: Directs the agent to execute `scripts/update.sh` from the repository root.

### skills/tone-guide: T0 (Inert)
- **Classification**: T0 (Inert — no scanned capability strings; instructional text only)
- **Artifact SHA-256**: `5ce7d10121bd397387d092ea5866c17fb22407dda45405a2b87c47f27750014f`
- **Endpoints detected**: None
- **Findings**: None (0 capability findings, 0 behavioral flags)
- **Details**: `skills/tone-guide/SKILL.md` contains purely instructional prose setting style guidelines for drafting and editing release notes and changelog entries. There are no executable scripts, outbound network calls, or privileged operations.
