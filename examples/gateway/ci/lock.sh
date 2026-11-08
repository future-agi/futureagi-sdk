#!/usr/bin/env bash
# Regenerate example-only locks on a cloud worker, never during the test phase.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root/examples/gateway/typescript"
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
cd "$root/examples/gateway/python"
uv pip compile --python-version 3.10 --generate-hashes requirements.in -o requirements.lock
mkdir -p "$root/out"
cp requirements.lock "$root/out/requirements.lock"
cp ../typescript/package-lock.json "$root/out/package-lock.json"
