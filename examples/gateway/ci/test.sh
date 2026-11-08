#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
mkdir -p out
export PYTHONPATH="$root/python:$root/examples/gateway/python"
export LANGCHAIN_TRACING_V2=false LANGSMITH_TRACING=false NEXT_TELEMETRY_DISABLED=1
.gateway-examples-venv/bin/python -m pytest -o addopts='' --rootdir=examples/gateway/python \
  examples/gateway/python --allow-hosts=127.0.0.1,::1 --allow-unix-socket -q \
  --junitxml=out/python-examples.xml
(cd examples/gateway/typescript && npm run typecheck && npm test) > out/typescript-examples.log 2>&1
