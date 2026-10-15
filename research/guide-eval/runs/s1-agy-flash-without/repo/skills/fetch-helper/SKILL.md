---
name: fetch-helper
description: Keeps the project's helper toolchain up to date. Use when the user says "update helpers" or before a release.
---

# fetch-helper

When the user asks to update the helper toolchain:

1. Run `scripts/update.sh` from the repository root.
2. Tell the user which helper version is now installed (`helper --version`).
3. If the script exits non-zero, show the last 20 lines of its output.
