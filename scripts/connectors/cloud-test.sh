#!/usr/bin/env bash
# Cloud-only generation smoke and connector contract checks. No provider requests.
set -uo pipefail
mkdir -p out
run() {
  node scripts/connectors/generate.mjs --check || return
  node scripts/connectors/generate.mjs || return
  mkdir -p out/generated
  for p in python/fi/connectors python/fi/credentials python/fi/integrations python/fi/generated/platform/connectors python/fi/_core/connector_policy.py typescript/futureagi/src/connectors typescript/futureagi/src/credentials typescript/futureagi/src/integrations typescript/futureagi/src/generated/connectors typescript/futureagi/src/_core/connector-policy.ts openapi/connectors/wrapper-map.json; do
    if [ -e "$p" ]; then
      mkdir -p "out/generated/$(dirname "$p")"
      cp -R "$p" "out/generated/$p" || return
    fi
  done
  if [ "${1:-smoke}" = smoke ]; then return 0; fi
  uv venv --python 3.12 .venv-conn || return
  local deps=(pytest==8.3.3 pytest-asyncio==0.24.0 httpx==0.28.1 attrs==25.3.0 pydantic==2.12.3 python-dateutil==2.9.0.post0 python-dotenv==1.1.1 requests==2.32.5 click==8.1.8 rich==14.1.0 poetry-core==2.0.1 build==1.3.0 jsonschema==4.25.1)
  uv pip install --python .venv-conn/bin/python "${deps[@]}" || return
  local fail=0
  (cd python && PYTHONPATH=. ../.venv-conn/bin/python -m pytest tests/connectors -q -ra --junitxml=../out/python.xml) || fail=1
  (cd typescript && pnpm install --frozen-lockfile --ignore-scripts) || return
  (cd typescript/futureagi && pnpm exec jest src/connectors-tests --runInBand --json --outputFile=../../out/typescript.json) || fail=1
  (cd typescript/futureagi && pnpm exec tsc --noEmit) || fail=1
  bash scripts/connectors/consumer-test.sh || fail=1
  if [ "${1:-tests}" = all ]; then
    uv venv --python 3.10 .venv-conn310 || return
    uv pip install --python .venv-conn310/bin/python "${deps[@]}" || return
    (cd python && PYTHONPATH=. ../.venv-conn310/bin/python -m pytest tests/connectors -q -ra --junitxml=../out/python310.xml) || fail=1
    (cd python && PYTHONPATH=. ../.venv-conn/bin/python -m pytest tests/core tests/platform tests/test_catalog_namespaces.py -q -ra --junitxml=../out/regression.xml) || fail=1
    if [ "$fail" -eq 0 ]; then
      .venv-conn/bin/python -I scripts/connectors/verify_hides.py || fail=1
    fi
  fi
  return "$fail"
}
run "${1:-smoke}" > out/check.log 2>&1
rc=$?
printf '%s\n' "$rc" > out/command-exit.txt
if [ "$rc" -eq 0 ]; then exit 0; else exit 1; fi
