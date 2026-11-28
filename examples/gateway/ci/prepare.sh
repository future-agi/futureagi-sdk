#!/usr/bin/env bash
# Dependencies are installed before the network-isolated tests.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
python_version=${PYTHON_VERSION:-3.12}
uv venv --python "$python_version" .gateway-examples-venv
uv pip sync --python .gateway-examples-venv/bin/python --require-hashes examples/gateway/python/requirements.lock
