#!/bin/sh
# Remove the build output directory and recreate it empty.
set -eu
BUILD_DIR="$(pwd)/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
echo "cleaned $BUILD_DIR"
