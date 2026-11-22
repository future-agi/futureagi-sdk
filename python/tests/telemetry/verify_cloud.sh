#!/usr/bin/env bash
# Execute on the assigned GCP VM, after syncing both integration worktrees.
# Usage: bash python/tests/telemetry/verify_cloud.sh /absolute/traceai/worktree
# No VM provisioning, authentication changes, publishing, or network exporters.
set -euo pipefail
if [[ "$(uname -s)" != Linux ]] || ! grep -qi Google /sys/class/dmi/id/product_name; then
  echo 'This verification must run on the assigned GCP VM, not a workstation.' >&2
  exit 2
fi
project=$(curl --fail --silent --show-error --max-time 5 --noproxy '*' -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/project/project-id)
[[ "$project" == fagi-omega-staging ]] || { echo 'Wrong qualification project.' >&2; exit 2; }
export PATH="$HOME/.local/bin:$PATH"
SDK_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TRACEAI_ROOT="${1:?Pass the synced traceAI integration worktree}"
[[ "$TRACEAI_ROOT" = /* && -f "$TRACEAI_ROOT/python/pyproject.toml" ]] || exit 2
ARTIFACTS="${SKT_ARTIFACTS:-$HOME/skt-artifacts}"
ENVS="${SKT_ENVS:-$HOME/skt-verification-envs}"
LOGS="$ARTIFACTS/verification"
mkdir -p "$ARTIFACTS" "$ENVS" "$LOGS"
rm -f "$ARTIFACTS/SHA256SUMS"
failures=0
run() {
  local name="$1"; shift
  if ("$@") > "$LOGS/$name.log" 2>&1; then
    printf 'PASS %s\n' "$name"
  else
    failures=$((failures + 1))
    printf 'FAIL %s (see %s)\n' "$name" "$LOGS/$name.log"
    tail -n 25 "$LOGS/$name.log"
  fi
}
traceai_python() {
  local v="$1" env="$ENVS/traceai-$1"
  uv venv --clear --python "$v" "$env" &&
    uv pip install --python "$env/bin/python" -e "$TRACEAI_ROOT/python[grpc]" \
      pytest pytest-asyncio pytest-mock responses respx pyyaml &&
    (cd "$TRACEAI_ROOT/python" && "$env/bin/python" -m pytest tests -q --ignore-glob='tests/test_framework_*')
}
for v in 3.10 3.11 3.12 3.13 3.14 3.15; do
  run "traceai-python-$v" traceai_python "$v"
done
run traceai-wheel uv build --wheel --out-dir "$ARTIFACTS" "$TRACEAI_ROOT/python"
sdk_python() {
  local v="$1" env="$ENVS/sdk-$1"
  local args=()
  uv venv --clear --python "$v" "$env" &&
    uv pip install --python "$env/bin/python" -e "$SDK_ROOT/python[otel]" \
      pytest pytest-asyncio pytest-mock responses respx pyyaml ruff || return
  if [[ "$v" = 3.11 ]]; then
    uv pip install --python "$env/bin/python" 'deepagents==0.4.11' || return
  else
    # The SDK qualifies this optional adapter on Python 3.11 only.
    args+=(--ignore=tests/r3_l10/test_deepagents.py)
  fi
  if [[ "$v" != 3.9 ]]; then
    # traceAI declares Python >=3.10. Test the actual local wheel on 3.11/3.13.
    uv pip install --python "$env/bin/python" "$ARTIFACTS"/fi_instrumentation_otel-*.whl || return
  fi
  (cd "$SDK_ROOT/python" && "$env/bin/python" -m pytest tests -q "${args[@]}")
}
for v in 3.9 3.11 3.13; do
  run "sdk-python-$v" sdk_python "$v"
  run "processor-budget-$v" "$ENVS/sdk-$v/bin/python" "$SDK_ROOT/python/tests/telemetry/bench_processor.py"
done
sdk_lint() {
  cd "$SDK_ROOT"
  # Match the repository CI rule set and working directory; use Python 3.9 syntax.
  "$ENVS/sdk-3.11/bin/ruff" check --isolated --target-version py39 \
    --select E,F,W,I --ignore E501 python/fi/telemetry python/tests/telemetry \
    python/fi/__init__.py python/fi/context/client.py python/fi/context/source.py \
    python/fi/context/sessions.py python/fi/context/adapters/deepagents.py \
    python/fi/skills/client.py python/fi/platform/_transport.py \
    python/fi/gateway/callbacks/opentelemetry.py
}
run sdk-ruff-changed sdk_lint
traceai_lint() {
  cd "$TRACEAI_ROOT"
  "$ENVS/sdk-3.11/bin/ruff" check --isolated --target-version py310 \
    --select E,F,W,I --ignore E501 python/fi_instrumentation/fi_types.py \
    python/fi_instrumentation/otel.py python/fi_instrumentation/instrumentation/runtime_attributes.py \
    python/fi_instrumentation/instrumentation/_image_cap.py \
    python/tests/test_provider_registry.py python/tests/test_runtime_attributes.py \
    python/tests/test_image_run_endpoints.py
}
run traceai-ruff-changed traceai_lint
run sdk-wheel uv build --wheel --out-dir "$ARTIFACTS" "$SDK_ROOT/python"
no_otel() {
  local env
  env="$(mktemp -d "$ENVS/no-otel-XXXXXX")"
  uv venv --python 3.11 "$env" &&
    uv pip install --python "$env/bin/python" "$ARTIFACTS"/futureagi-*.whl pytest &&
    "$env/bin/python" -c 'import importlib.util; assert importlib.util.find_spec("opentelemetry") is None' &&
    (cd "$SDK_ROOT/python" && "$env/bin/python" -m pytest tests/telemetry/test_no_otel.py -q)
}
run sdk-no-otel-wheel no_otel
sdk_typescript() {
  cd "$SDK_ROOT/typescript/futureagi"
  pnpm install --ignore-workspace --no-frozen-lockfile --ignore-scripts &&
    pnpm run typecheck && pnpm run build && pnpm exec jest --runInBand &&
    npm pack --ignore-scripts --pack-destination "$ARTIFACTS"
}
run sdk-typescript sdk_typescript
traceai_typescript() {
  cd "$TRACEAI_ROOT/typescript"
  pnpm --filter @traceai/fi-core... --filter @traceai/fi-semantic-conventions... install --ignore-scripts --no-frozen-lockfile &&
    pnpm --filter @traceai/fi-semantic-conventions run build &&
    pnpm --filter @traceai/fi-core run build &&
    pnpm --filter @traceai/fi-semantic-conventions run test --runInBand &&
    pnpm --filter @traceai/fi-core run test --runInBand &&
    pnpm --filter @traceai/fi-core run test:provider &&
    (cd packages/fi-semantic-conventions && pnpm pack --pack-destination "$ARTIFACTS") &&
    (cd packages/fi-core && pnpm pack --pack-destination "$ARTIFACTS")
}
run traceai-typescript traceai_typescript
packed_typescript() {
  local fixture
  fixture="$(mktemp -d "$ENVS/packed-typescript-XXXXXX")"
  cp "$SDK_ROOT/python/tests/telemetry/packed_traceai.mjs" "$fixture/probe.mjs"
  cd "$fixture"
  printf '{"name":"local-package-qualification","private":true}\n' > package.json
  npm install --ignore-scripts --no-audit --no-fund \
    "$ARTIFACTS"/future-agi-sdk-*.tgz "$ARTIFACTS"/traceai-fi-core-*.tgz \
    "$ARTIFACTS"/traceai-fi-semantic-conventions-*.tgz || return
  for mode in on load_only off; do
    node probe.mjs "$mode" || return
  done
  cp "$SDK_ROOT/python/tests/telemetry/packed_traceai_opt_in.mjs" "$fixture/opt-in.mjs"
  for mode in off on; do
    node opt-in.mjs "$mode" || return
  done
}
run packed-typescript-interop packed_typescript
run sdk-vector-parity cmp "$SDK_ROOT/python/tests/telemetry/vectors/processor_v1.json" \
  "$SDK_ROOT/typescript/futureagi/src/__tests__/telemetry/vectors/processor_v1.json"
run traceai-vector-parity cmp "$SDK_ROOT/python/tests/telemetry/vectors/processor_v1.json" \
  "$TRACEAI_ROOT/typescript/packages/fi-core/src/__tests__/vectors/processor_v1.json"
printf 'Verification failures: %s; logs and packages: %s\n' "$failures" "$ARTIFACTS"
if [[ "$failures" = 0 ]]; then
  (cd "$ARTIFACTS" && sha256sum ./*.whl ./*.tgz > SHA256SUMS)
fi
[[ "$failures" = 0 ]]
