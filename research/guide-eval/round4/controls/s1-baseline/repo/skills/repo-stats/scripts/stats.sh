#!/bin/sh
# Lines of code per language, excluding vendored and generated files.
set -e
npx --yes cloc@latest --quiet --md --exclude-dir=node_modules,vendor,build,dist .
