#!/usr/bin/env bash
# Regenerate the example dependency lock outside the test phase.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root/examples/gateway/python"
uv pip compile --python-version 3.10 --generate-hashes requirements.in -o requirements.lock
mkdir -p "$root/out"
cp requirements.lock "$root/out/requirements.lock"
