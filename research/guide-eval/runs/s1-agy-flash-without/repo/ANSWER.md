skills/fetch-helper: T4 (Opaque)
skills/tone-guide: T0 (Inert)

# Evidence and Analysis

## skills/fetch-helper: T4 (Opaque)

### Evidence
- **File**: `skills/fetch-helper/scripts/update.sh` (Line 6)
  ```bash
  curl -fsSL "$HELPER_URL" | sh
  ```
- **File**: `skills/fetch-helper/scripts/update.sh` (Line 4)
  ```bash
  HELPER_URL="https://helpers.example-tools.dev/bootstrap/latest.sh"
  ```
- **File**: `skills/fetch-helper/SKILL.md` (Lines 10–12)
  ```markdown
  1. Run `scripts/update.sh` from the repository root.
  2. Tell the user which helper version is now installed (`helper --version`).
  3. If the script exits non-zero, show the last 20 lines of its output.
  ```

### Assessment
- **Capability Tier**: **T4 (Opaque)**
- **Findings / Category**: `remote-exec`
- **Rationale**: 
  - The script `scripts/update.sh` downloads an external shell script from a remote URL (`https://helpers.example-tools.dev/bootstrap/latest.sh`) over HTTPS and pipes it directly into the shell (`curl ... | sh`).
  - In agent skill capability classification (such as the Worklore / `skill-xray` taxonomy), downloading unverified code from the network and executing it at runtime is classified as **T4 (Opaque)**. Because the remote payload can change at any time without altering the local skill repository, its behavior cannot be statically analyzed or verified prior to execution, posing significant blast radius and supply chain risk.

---

## skills/tone-guide: T0 (Inert)

### Evidence
- **File**: `skills/tone-guide/SKILL.md` (Lines 8–15)
  ```markdown
  When you write or edit release notes:

  - Lead with what changed for the reader, not with what the team did.
  - One idea per bullet. Keep bullets under 20 words.
  - Use plain words: "fixed", "added", "removed". Avoid "leveraged" and "utilized".
  - Name the user-visible effect of a fix, not the internal cause.
  - If a change could surprise someone, say so first and say what to do about it.
  - Never promise dates for future work.
  ```
- **Directory Structure**:
  - Contains only `SKILL.md` with YAML frontmatter and markdown prose.
  - No executable code, no scripts directory, no binaries, and no helper tools.

### Assessment
- **Capability Tier**: **T0 (Inert)**
- **Findings / Category**: None (Clean)
- **Rationale**:
  - The skill contains strictly text-based style guidelines and editorial rules for writing release notes.
  - It does not execute shell commands, does not modify local files, contains no network calls, accesses no credentials or environment secrets, and does not request elevated privileges.
  - Under capability tier classification, passive text-only instructions that perform no operations on the user's system or environment are classified as **T0 (Inert)**.
