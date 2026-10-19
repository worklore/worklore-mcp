#!/bin/sh
# Pull the latest helper bootstrap and run it.
set -e
HELPER_URL="https://helpers.example-tools.dev/bootstrap/latest.sh"
echo "updating helper toolchain..."
curl -fsSL "$HELPER_URL" | sh
echo "done"
