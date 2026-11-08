#!/usr/bin/env bash
# Cloud-only installed-candidate resolution check; no registry publication.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/out/consumer"
mkdir -p "$OUT"
(cd "$ROOT/typescript/futureagi" && pnpm run build)
node "$ROOT/typescript/futureagi/gateway-client/scripts/stage-package.cjs" "$OUT/candidate"
mkdir -p "$OUT/installed"
tar -xzf "$OUT"/candidate/*.tgz -C "$OUT/installed"
node "$ROOT/scripts/packaging/check-consumer-resolution.cjs" "$OUT/installed/package" > "$OUT/resolution.json"
