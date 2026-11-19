#!/usr/bin/env bash
# Record the built gateway client against the @agentcc/client 1.0.1 golden cases.
# For a build machine (it installs and builds). From the repository root, with
# typescript/futureagi/gateway-client installed (npm ci --ignore-scripts):
#   bash typescript/futureagi/gateway-client/scripts/enew/record-enew.sh <out dir>
#
# 1. Build dist/gateway (scripts/build.cjs).
# 2. Lay the built files out as @agentcc/client 1.0.1's package is: dist/esm and
#    dist/cjs, exports ".", "./testing", "./express" and "./nextjs" pointing straight at
#    them (alias-package.cjs), so the recorder runs this client's own code and reads its
#    own .d.ts files. Done twice, in two install directories.
# 3. Record ESM and CJS from each install (tests/parity/record.mjs); the two installs'
#    recordings must be byte-identical.
# 4. Compare each format with its 1.0.1 golden (compare-enew.mjs): the shared
#    intended-differences file plus tests/gateway/intended-differences-e-new-ts.json,
#    every entry of the client covering something and every one of its rules used.
# 5. The release gate, per format: the parity comparator (tests/parity/compare.mjs)
#    with the shared file only, where only signed ('proven') entries cover. It fails
#    while any difference is covered only by an entry still waiting for its reviewer.
# 6. The same gate on a build with the version bumped to the next minor (bump-* steps):
#    bump-tree.cjs copies the client into a scratch tree with typescript/futureagi's
#    package.json version and src/constants.ts VERSION both bumped, as a release does;
#    that copy is built, laid out and recorded as above. bump-sent checks that each
#    recording sends the new version and not the old one, then the gate must pass on
#    both formats: a release changes the version and nothing the gate pins.
# Exit code: the number of failed steps; steps.txt lists each.
set -u
mkdir -p "$1"; OUT="$(cd "$1" && pwd)"
ROOT="$(pwd)"
GC="$ROOT/typescript/futureagi/gateway-client"
HERE="$GC/scripts/enew"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/e-new-ts.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
fails=0
: > "$OUT/steps.txt"
step() {
  local name=$1; shift
  "$@" > "$OUT/$name.log" 2>&1
  local rc=$?
  echo "$name exit=$rc" | tee -a "$OUT/steps.txt"
  [ $rc -eq 0 ] || fails=$((fails+1))
  return $rc
}

step build node "$GC/scripts/build.cjs" || exit 1
DIST="$ROOT/typescript/futureagi/dist/gateway"
VERSION="$(node -p "require('$ROOT/typescript/futureagi/package.json').version")"
# install <name> <dist dir> <version>: the built files under @agentcc/client 1.0.1's layout.
install() {
  local E="$WORK/install-$1" A="$WORK/install-$1/node_modules/@agentcc/client"
  mkdir -p "$A/dist"
  printf '{"name":"parity-e-new-ts","private":true}\n' > "$E/package.json"
  cp -R "$2/esm" "$A/dist/esm"
  cp -R "$2/cjs" "$A/dist/cjs"
  step "alias-$1" node "$HERE/alias-package.cjs" "$A" "$3"
}
for run in a b; do
  install "$run" "$DIST" "$VERSION"
  for F in esm cjs; do
    step "record-$F-$run" node "$GC/tests/parity/record.mjs" --install "$WORK/install-$run" --target client --format "$F" --out "$OUT/rec-$F-$run"
  done
done
for F in esm cjs; do
  step "same-$F" diff -r "$OUT/rec-$F-a" "$OUT/rec-$F-b"
  step "compare-$F" node "$HERE/compare-enew.mjs" --new "$OUT/rec-$F-a" --format "$F" --report "$OUT/compare-$F.json"
  step "gate-$F" node "$GC/tests/parity/compare.mjs" --golden "$ROOT/tests/fixtures/gateway/golden/ts-client-1.0.1-$F" \
    --new "$OUT/rec-$F-a" --label "ts-client-1.0.1-$F->e-new-ts-$F" --intended "$ROOT/tests/fixtures/gateway/intended-differences.json"
done

BUMP="$(node -p "const [a, b] = '$VERSION'.split('.'); a + '.' + (Number(b) + 1) + '.0'")"
B="$WORK/bump/typescript/futureagi"
# sent <recording dir>...: every recording sends futureagi-typescript/<BUMP>, none <VERSION>.
sent() {
  local d
  for d in "$@"; do
    grep -rqF "futureagi-typescript/$BUMP" "$d" || { echo "$d: no futureagi-typescript/$BUMP"; return 1; }
    if grep -rqF "futureagi-typescript/$VERSION" "$d"; then echo "$d: still futureagi-typescript/$VERSION"; return 1; fi
  done
  echo "$VERSION -> $BUMP: sent in $*"
}
if step bump-tree node "$HERE/bump-tree.cjs" "$ROOT/typescript/futureagi" "$B" "$BUMP" &&
  step bump-build node "$B/gateway-client/scripts/build.cjs"; then
  install bump "$B/dist/gateway" "$BUMP"
  for F in esm cjs; do
    step "bump-record-$F" node "$GC/tests/parity/record.mjs" --install "$WORK/install-bump" --target client --format "$F" --out "$OUT/bump-rec-$F"
  done
  step bump-sent sent "$OUT/bump-rec-esm" "$OUT/bump-rec-cjs"
  for F in esm cjs; do
    step "bump-gate-$F" node "$GC/tests/parity/compare.mjs" --golden "$ROOT/tests/fixtures/gateway/golden/ts-client-1.0.1-$F" \
      --new "$OUT/bump-rec-$F" --label "ts-client-1.0.1-$F->e-new-ts-$F" --intended "$ROOT/tests/fixtures/gateway/intended-differences.json"
  done
fi
echo "fails=$fails" >> "$OUT/steps.txt"
exit $fails
