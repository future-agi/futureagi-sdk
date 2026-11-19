#!/usr/bin/env bash
# Record the E-OLD goldens twice and prove the two runs byte-identical.
# Runs on a disposable Linux VM, never on a
# workstation: it downloads from PyPI and npm and builds two git trees.
#
# Usage (from the repository root): record-e-old.sh <out-dir> <work-dir> <src-client-patch-source> <src-release-source>
#
#   1. fetch-artifacts.sh: the PyPI wheel, the five published npm tarballs, the
#      client-patch-source / release-source builds, registry evidence; summarize_artifacts.py checks
#      every hash against the registry's published value.
#   2. One install per target: a venv with the 1.0.0 wheel under
#      constraints-py.txt; npm scratch projects from e-old/npm/*/package.json
#      (`npm ci` when the committed package-lock.json is present).
#   3. Each target recorded twice, each run in a fresh process, then compared
#      file by file with cmp. Run 2 records from a copy of the recorders at
#      another path, with the npm installs copied and the venv built again
#      elsewhere, so the identity also proves no golden depends on where it was
#      made (and each recorder refuses to write a local path). Exit 0 only if
#      every hash matched and every file of run 1 equals run 2.
set -euo pipefail

OUT=${1:?out dir (must not exist yet)}
WORK=${2:?work dir (must not exist yet)}
if [ -e "$OUT" ] || [ -e "$WORK" ]; then echo "record-e-old: $OUT or $WORK exists; pass fresh directories" >&2; exit 2; fi
SRC05=${3:?client-patch-source export}
SRC98=${4:?release-source export}
REPO=$(pwd)
FIX="$REPO/tests/fixtures/gateway/e-old"
PY=/usr/bin/python3.12
mkdir -p "$OUT/logs" "$WORK"
OUT=$(cd "$OUT" && pwd)
WORK=$(cd "$WORK" && pwd)

bash "$FIX/fetch-artifacts.sh" "$OUT/fetch" "$WORK" "$SRC05" "$SRC98"
"$PY" -I "$FIX/summarize_artifacts.py" "$OUT/fetch" "$WORK" "$SRC98" | tee "$OUT/hash-check.txt"

export npm_config_userconfig="$WORK/empty-npmrc" npm_config_cache="$WORK/npm-cache"
export npm_config_audit=false npm_config_fund=false npm_config_update_notifier=false
export npm_config_registry=https://registry.npmjs.org/

# --- installs ---------------------------------------------------------------
uv venv "$WORK/py-e-old" --python "$PY" -q
uv pip install --python "$WORK/py-e-old/bin/python" -c "$FIX/constraints-py.txt" \
  "$(ls "$WORK"/pypi/agentcc-1.0.0-py3-none-any.whl)" jsonschema > "$OUT/logs/py-install.log" 2>&1
uv pip freeze --python "$WORK/py-e-old/bin/python" > "$OUT/py-freeze.txt"

# Run 2's places: the recorders and fixtures copied to another checkout path,
# a second venv from the same pinned files (a venv does not move).
ALT="$WORK/relocated/checkout"
for d in python/tests/gateway typescript/futureagi/gateway-client/tests/parity tests/fixtures/gateway; do
  mkdir -p "$ALT/$(dirname "$d")"
  cp -R "$REPO/$d" "$ALT/$d"
done
uv venv "$WORK/relocated/py-e-old" --python "$PY" -q
uv pip install --python "$WORK/relocated/py-e-old/bin/python" -c "$FIX/constraints-py.txt" \
  "$(ls "$WORK"/pypi/agentcc-1.0.0-py3-none-any.whl)" jsonschema > "$OUT/logs/py-install-run2.log" 2>&1
uv pip freeze --python "$WORK/relocated/py-e-old/bin/python" > "$OUT/py-freeze-run2.txt"

mkdir -p "$OUT/npm-locks"
for target in client-1.0.0 client-1.0.1 integrations-1.0.0; do
  dir="$WORK/ts/$target"
  mkdir -p "$dir"
  cp "$FIX/npm/$target/package.json" "$dir/"
  [ "$target" = client-1.0.1 ] && cp "$WORK/tarballs/local-client-patch-source/agentcc-client-1.0.1.tgz" "$dir/"
  if [ -f "$FIX/npm/$target/package-lock.json" ]; then
    cp "$FIX/npm/$target/package-lock.json" "$dir/"
    (cd "$dir" && npm ci --ignore-scripts --legacy-peer-deps > "$OUT/logs/npm-$target.log" 2>&1)
  else
    (cd "$dir" && npm install --ignore-scripts --legacy-peer-deps > "$OUT/logs/npm-$target.log" 2>&1)
  fi
  mkdir -p "$OUT/npm-locks/$target"
  cp "$dir/package-lock.json" "$OUT/npm-locks/$target/"
done
cp -R "$WORK/ts" "$WORK/relocated/ts"

# --- record twice -----------------------------------------------------------
record_run() {  # <run> <checkout> <venv> <npm installs>
  local run=$1 co=$2 venv=$3 ts=$4 fmt
  (cd "$co/python/tests/gateway" && "$venv/bin/python" -m parity.record --root agentcc \
    --out "$OUT/$run/py-agentcc-1.0.0") 2>> "$OUT/logs/record-$run.log"
  for fmt in esm cjs; do
    for t in "client-1.0.0 client ts-client-1.0.0" "client-1.0.1 client ts-client-1.0.1" \
      "integrations-1.0.0 integrations ts-integrations-1.0.0"; do
      set -- $t
      node "$co/typescript/futureagi/gateway-client/tests/parity/record.mjs" --install "$ts/$1" \
        --target "$2" --format "$fmt" --out "$OUT/$run/$3-$fmt" 2>> "$OUT/logs/record-$run.log"
    done
  done
}
record_run run1 "$REPO" "$WORK/py-e-old" "$WORK/ts"
record_run run2 "$ALT" "$WORK/relocated/py-e-old" "$WORK/relocated/ts"

# --- byte identity ----------------------------------------------------------
status=0
: > "$OUT/byte-identity.txt"
(cd "$OUT/run1" && find . -type f | sort) > "$OUT/run1-files.txt"
(cd "$OUT/run2" && find . -type f | sort) > "$OUT/run2-files.txt"
if ! cmp -s "$OUT/run1-files.txt" "$OUT/run2-files.txt"; then echo "FILE SETS DIFFER" >> "$OUT/byte-identity.txt"; status=1; fi
if ! cmp -s "$OUT/py-freeze.txt" "$OUT/py-freeze-run2.txt"; then echo "VENVS DIFFER" >> "$OUT/byte-identity.txt"; status=1; fi
while read -r f; do
  if cmp -s "$OUT/run1/$f" "$OUT/run2/$f"; then r=identical; else r=DIFFERENT; status=1; fi
  printf '%s  %s  %s\n' "$(sha256sum "$OUT/run1/$f" | cut -d' ' -f1)" "$r" "$f" >> "$OUT/byte-identity.txt"
done < "$OUT/run1-files.txt"
grep -q MATCH "$OUT/hash-check.txt" && ! grep -q MISMATCH "$OUT/hash-check.txt" || status=1
echo "record-e-old: files=$(wc -l < "$OUT/run1-files.txt") different=$(grep -c DIFFERENT "$OUT/byte-identity.txt" || true) status=$status"
exit $status
