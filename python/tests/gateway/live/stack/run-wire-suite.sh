#!/usr/bin/env bash
# The live wire proof, as one command. Run it only on a disposable build machine
# (it builds the gateway and starts servers), never on a developer's workstation.
#
#   GW_SRC=<agentcc gateway repo checked out at live-gateway-source> \
#     bash python/tests/gateway/live/stack/run-wire-suite.sh <out dir>
#
# From the futureagi-sdk repository root. Steps (GW_LIVE_STEPS, default all):
#   py       python/tests/gateway/live (pytest; needs GW_PY with fi.gateway, pytest, openai)
#   ts       typescript/futureagi/gateway-client/tests/live (tsc, then jest with its own
#            config; tests/live/stock runs the stock openai-node SDK when installed there)
#   browser  the browser CORS preflight in Chromium, Firefox and WebKit (needs GW_PLAYWRIGHT
#            and PLAYWRIGHT_BROWSERS_PATH)
# Starts: the mock upstream (127.0.0.1:18101), the gateway (127.0.0.1:8090, built here
# from GW_SRC/agentcc-gateway), the wire tap (127.0.0.1:8091). Makes three virtual keys
# the config registers, and mints a fourth with an admin token made for this run. Every secret it makes stays in a private
# state directory outside <out dir>; evidence records tokens only as sha256 prefixes.
# Stops everything it started on exit. Exit code: the number of failed steps.
set -u
[ -n "${1:-}" ] || { echo "usage: GW_SRC=<repo> $0 <out dir>" >&2; exit 2; }
mkdir -p "$1"; OUT="$(cd "$1" && pwd)"
WT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
LIVE="$WT/python/tests/gateway/live"
GC="$WT/typescript/futureagi/gateway-client"
PY="${GW_PY:-python3}"
# Content pin of the reviewed gateway tree (git's raw tree-object bytes).
PIN="1725532bd8c6648b94d45044b08446c89ed2d0b48f21b712f3f17beeceaa3b71"
STEPS="${GW_LIVE_STEPS:-py ts browser}"
STATE="$(mktemp -d "${TMPDIR:-/tmp}/gwlive-state.XXXXXX")"; chmod 700 "$STATE"
mkdir -p "$OUT/evidence"
: > "$OUT/steps.txt"
fails=0
PIDS=""
cleanup() { for p in $PIDS; do kill "$p" 2>/dev/null; done; sleep 1; for p in $PIDS; do kill -9 "$p" 2>/dev/null; done; rm -rf "$STATE"; }
trap cleanup EXIT
step() {
  local name=$1; shift
  "$@" > "$OUT/$name.log" 2>&1
  local rc=$?
  echo "$name exit=$rc" | tee -a "$OUT/steps.txt"
  [ $rc -eq 0 ] || fails=$((fails+1))
  return $rc
}
ctl() { "$PY" -I "$LIVE/stack/stack_ctl.py" "$@"; }

# 0. Provenance: the gateway source must be the reviewed content, and clean.
[ -n "${GW_SRC:-}" ] || { echo "GW_SRC is not set" >&2; exit 2; }
GW_HEAD="$(git -C "$GW_SRC" rev-parse HEAD)"
GW_CONTENT="$(git -C "$GW_SRC" cat-file tree HEAD:agentcc-gateway | sha256sum | cut -d ' ' -f1)"
[ "$GW_CONTENT" = "$PIN" ] || { echo "gateway source content does not match the reviewed pin" >&2; exit 2; }
[ -z "$(git -C "$GW_SRC" status --porcelain -- agentcc-gateway)" ] || { echo "gateway source is modified" >&2; exit 2; }
{
  echo "gateway_head=$GW_HEAD"
  echo "gateway_tree=$(git -C "$GW_SRC" rev-parse HEAD:agentcc-gateway)"
  echo "sdk_head=$(git -C "$WT" rev-parse HEAD) (OMEGA_EXEC_SOURCE_HEAD=${OMEGA_EXEC_SOURCE_HEAD:-unset})"
  echo "go=$(cd "$GW_SRC/agentcc-gateway" && go version)"
  echo "python=$("$PY" --version 2>&1)"; echo "node=$(node --version)"; uname -a
} > "$OUT/env.txt" 2>&1

# 1. Build the gateway at the pin.
step build bash -c "cd '$GW_SRC/agentcc-gateway' && go build -trimpath -o '$STATE/agentcc' ./cmd/agentcc" || exit 1

# 2. Bring the stack up.
export MOCK_BLOCK_WORD="kumquatforbidden"
export MOCK_URL="http://127.0.0.1:18101"
export GW_OP_EQ='$eq' # see gateway.yaml conditional_routes
MOCK_UPSTREAM_KEY="$(ctl secret mockup-)"; export MOCK_UPSTREAM_KEY
AGENTCC_ADMIN_TOKEN="$(ctl secret admin-)"; export AGENTCC_ADMIN_TOKEN
GW_LIVE_KEY_PLAIN="$(ctl secret sk-agentcc-live-)"; export GW_LIVE_KEY_PLAIN
GW_LIVE_KEY_OVERRIDE="$(ctl secret sk-agentcc-live-)"; export GW_LIVE_KEY_OVERRIDE
GW_LIVE_KEY_FALLBACK="$(ctl secret sk-agentcc-live-)"; export GW_LIVE_KEY_FALLBACK
"$PY" -I "$LIVE/stack/mock_upstream.py" --port 18101 --log "$OUT/evidence/mock-requests.jsonl" > "$OUT/mock.log" 2>&1 &
PIDS="$PIDS $!"
"$STATE/agentcc" -config "$LIVE/stack/gateway.yaml" > "$OUT/gateway.log" 2>&1 &
PIDS="$PIDS $!"
step up-gateway ctl wait http://127.0.0.1:8090/healthz 60 || exit 1
"$PY" -I "$LIVE/stack/wiretap.py" --port 8091 --target 127.0.0.1:8090 --log "$OUT/evidence/tap-requests.jsonl" > "$OUT/tap.log" 2>&1 &
PIDS="$PIDS $!"
step up-mock ctl wait "$MOCK_URL/v1/models" 30 || exit 1
step up-tap ctl wait http://127.0.0.1:8091/healthz 30 || exit 1
step mint ctl mint http://127.0.0.1:8090 "$STATE/keys.json" || exit 1
step org-config ctl org-config http://127.0.0.1:8090 org-live cache || exit 1
step org-config-fallback ctl org-config http://127.0.0.1:8090 org-fallback fallback || exit 1

export FI_GATEWAY_LIVE_BASE_URL="http://127.0.0.1:8090"
export FI_GATEWAY_LIVE_TAP_URL="http://127.0.0.1:8091"
export FI_GATEWAY_LIVE_MOCK_URL="$MOCK_URL"
export FI_GATEWAY_LIVE_KEYS="$STATE/keys.json"
export FI_GATEWAY_LIVE_EVIDENCE="$OUT/evidence"
export FI_GATEWAY_LIVE_BLOCK_WORD="$MOCK_BLOCK_WORD"
FI_GATEWAY_LIVE_UPSTREAM_KEY_SHA12="$(ctl sha12 "$MOCK_UPSTREAM_KEY")"; export FI_GATEWAY_LIVE_UPSTREAM_KEY_SHA12
export FI_GATEWAY_BASE_URL="http://127.0.0.1:8090" # the base URL both live suites use
unset MOCK_UPSTREAM_KEY AGENTCC_ADMIN_TOKEN GW_LIVE_KEY_PLAIN GW_LIVE_KEY_OVERRIDE GW_LIVE_KEY_FALLBACK # the suites read the keys file

for s in $STEPS; do
  case "$s" in
    py) step py-live "$PY" -m pytest -q -p no:cacheprovider -rA "$LIVE" --junitxml="$OUT/py-live.xml" ;;
    ts) step ts-typecheck node "$GC/node_modules/typescript/bin/tsc" -p "$GC/tests/live/tsconfig.live.json" --noEmit
        step ts-live node "$GC/node_modules/jest/bin/jest.js" -c "$GC/tests/live/jest.live.config.cjs" \
          --runInBand --ci --json --outputFile="$OUT/ts-live.json"
        step ts-names sh -c "node '$GC/tests/live/check-live-names.cjs' '$OUT/ts-live.json' > '$OUT/evidence/ts-live-names.json'" ;;
    browser)
      step browser-bundle node "$GC/node_modules/esbuild/bin/esbuild" "$GC/tests/live/browser/cors-entry.ts" \
        --bundle --format=esm --platform=browser --target=es2020 --outfile="$OUT/browser/bundle.js" &&
      step browser-cors node "$GC/tests/live/browser/cors-browser.cjs" "$OUT/browser/bundle.js" \
        "$OUT/evidence/ts/browser-cors.json" ;;
    *) echo "unknown step $s" >&2; fails=$((fails+1)) ;;
  esac
done

# 3. What the gateway logged, for the record (it never logs a raw key).
cp "$OUT/gateway.log" "$OUT/evidence/gateway.log" 2>/dev/null
echo "fails=$fails" >> "$OUT/steps.txt"
exit $fails
