#!/usr/bin/env bash
# Dependencies are installed before the network-isolated tests.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
python_version=${PYTHON_VERSION:-3.12}
uv venv --python "$python_version" .gateway-examples-venv
uv pip sync --python .gateway-examples-venv/bin/python --require-hashes examples/gateway/python/requirements.lock
(cd typescript/futureagi/gateway-client && npm ci --ignore-scripts --no-audit --no-fund)
node typescript/futureagi/gateway-client/scripts/build.cjs
(cd examples/gateway/typescript && npm ci --ignore-scripts --no-audit --no-fund)
# Resolve the real package export map and built gateway bytes, not source aliases.
sdk=examples/gateway/typescript/node_modules/@future-agi/sdk
mkdir -p "$sdk/dist"
cp typescript/futureagi/package.json "$sdk/package.json"
cp -R typescript/futureagi/dist/gateway "$sdk/dist/"
