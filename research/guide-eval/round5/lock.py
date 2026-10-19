#!/usr/bin/env python3
"""usage: lock.py <lockfile> <cmd...>  — run cmd holding an exclusive lock (flock replacement for macOS)."""
import fcntl, subprocess, sys
with open(sys.argv[1], "w") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    sys.exit(subprocess.call(sys.argv[2:]))
