#!/usr/bin/env bash
# The gateway client's default suite, as a build machine runs it:
#   bash typescript/futureagi/gateway-client/scripts/run-suite.sh <out dir>
# For every Node binary directory in GW_NODES (default: the node on PATH):
# jest --runInBand (--json), the 1.0.1 test-name check, and the parity
# comparator and golden hygiene node tests (tests/parity/compare.test.mjs,
# hygiene.test.mjs); then both typechecks (sources, and sources plus tests)
# with the first Node.
# Exit code: the number of failed steps.
set -u
mkdir -p "$1"; OUT="$(cd "$1" && pwd)"
GC="$(cd "$(dirname "$0")/.." && pwd)"
cd "$GC"
NODES="${GW_NODES:-$(dirname "$(command -v node)")}"
fails=0
step() { local name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; local rc=$?; echo "$name exit=$rc" | tee -a "$OUT/steps.txt"; [ $rc -eq 0 ] || fails=$((fails+1)); }
first=""
for N in $NODES; do
  V=$("$N/node" --version); [ -n "$first" ] || first=$N
  JEST=$("$N/node" -p 'require.resolve("jest/bin/jest")')
  step "jest-$V" "$N/node" "$JEST" -c jest.config.cjs --runInBand --ci --json --outputFile="$OUT/jest-$V.json"
  step "names-$V" sh -c "\"$N/node\" scripts/check-test-names.cjs \"$OUT/jest-$V.json\" > \"$OUT/names-$V.json\""
  step "parity-$V" "$N/node" --test tests/parity/compare.test.mjs tests/parity/hygiene.test.mjs
done
TSC=$("$first/node" -p 'require.resolve("typescript/bin/tsc")')
step tsc-src "$first/node" "$TSC" -p tsconfig.json --noEmit
step tsc-tests "$first/node" "$TSC" -p tsconfig.typecheck.json
"$first/node" --version > "$OUT/env.txt"; "$first/node" -p 'require("typescript/package.json").version + " typescript; " + require("jest/package.json").version + " jest; " + require("ts-jest/package.json").version + " ts-jest"' >> "$OUT/env.txt" 2>&1
exit $fails
