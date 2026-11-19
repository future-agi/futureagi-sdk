#!/usr/bin/env bash
# Packed-tarball proofs for the gateway subpaths.
# For a build machine (it installs from the registry, builds and packs). From the repository root:
#   bash typescript/futureagi/gateway-client/scripts/pack-checks.sh <out dir>
# Needs: typescript/futureagi installed (pnpm install --frozen-lockfile
# --ignore-scripts), gateway-client installed (npm ci --ignore-scripts), and
# GW_NODES = Node bin directories (default: the node on PATH).
#
# 1. Root build (pnpm run build, which runs build:gateway), stage-package.cjs
#    (the candidate: gateway exports, mappings and optional peer kept), npm pack.
# 2. Per Node: a fresh consumer installs the tarball with react 18;
#    check-default-resolution.cjs loads all five subpaths with no custom
#    resolver condition, then import() and require() every subpath, use each
#    one, and check-smoke.cjs judges the result against
#    tests/gateway/api-snapshot.json.
# 3. React install matrix (each Node): no peers; react 17, 18, 19; an existing
#    tree with react 17 and openai 4. Never --legacy-peer-deps; step 7 fails
#    on any ERESOLVE line in any install log.
# 4. tsc fixtures under node10, node16 (.mts and .cts) and bundler against the
#    installed tarball, with skipLibCheck false; and node10 importing the root
#    entry, with skipLibCheck true (the root entry's .d.ts files come from the
#    root package's own build, not from gateway-client).
# 5. esbuild browser bundles of ./gateway, ./gateway/react, ./gateway/nextjs
#    with metafiles, judged by check-metafile.cjs.
# 6. With GW_PLAYWRIGHT set: D-18 in Chromium, Firefox and WebKit
#    (scripts/browser/d18-browser.cjs).
# Every step resolves with the default conditions only: no --conditions,
# customConditions or bundler condition names.
# Exit code: the number of failed steps; steps.txt lists each.
set -u
mkdir -p "$1"; OUT="$(cd "$1" && pwd)"
WT="$(pwd)"
FA="$WT/typescript/futureagi"
GC="$FA/gateway-client"
C="$GC/scripts/consumer"
SNAP="$GC/tests/gateway/api-snapshot.json"
NODES="${GW_NODES:-$(dirname "$(command -v node)")}"
FIRST="${NODES%% *}"
LAST="${NODES##* }"
TSC_VERSION="5.8.3"; TYPES_REACT="18.3.12"; TYPES_NODE="20.19.2"
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
consumer() { # <dir> <node bin> <npm install args...>
  local dir=$1 nb=$2; shift 2
  rm -rf "$dir"; mkdir -p "$dir"
  cp "$C"/*.cjs "$C"/*.mjs "$dir"/
  printf '{"name":"consumer","version":"0.0.0","private":true}\n' > "$dir/package.json"
  (cd "$dir" && PATH="$nb:$PATH" npm install --ignore-scripts --no-audit --no-fund "$@")
}

# 1. build and pack
step build-root bash -c "cd '$FA' && pnpm run build"
step stage bash -c "node '$GC/scripts/stage-package.cjs' '$OUT/stage' > '$OUT/tarball.txt'"
TARBALL="$(cat "$OUT/tarball.txt")"
sha256sum "$TARBALL" > "$OUT/tarball.sha256"
tar -tzf "$TARBALL" | sort > "$OUT/tarball-files.txt"
cp "$OUT/stage/package.json" "$OUT/packed-package.json"
step mode-on bash -c "grep -qx '{\"gateway\":\"on\"}' '$OUT/stage/mode.json' && grep -q '^package/dist/gateway/cjs/index.js$' '$OUT/tarball-files.txt' && grep -q '^package/dist/gateway/esm/index.js$' '$OUT/tarball-files.txt'"

# 2. ESM and CJS smoke per Node
for N in $NODES; do
  V=$("$N/node" --version)
  D="$OUT/work/smoke-$V"
  step "install-$V" consumer "$D" "$N" "$TARBALL" react@18.3.1 react-dom@18.3.1
  step "default-resolution-$V" bash -c "cd '$D' && NODE_OPTIONS= '$N/node' check-default-resolution.cjs"
  step "smoke-esm-$V" bash -c "cd '$D' && '$N/node' smoke.mjs > '$OUT/smoke-esm-$V.json'"
  step "smoke-cjs-$V" bash -c "cd '$D' && '$N/node' smoke.cjs > '$OUT/smoke-cjs-$V.json'"
  step "check-esm-$V" node "$C/check-smoke.cjs" "$SNAP" "$OUT/smoke-esm-$V.json"
  step "check-cjs-$V" node "$C/check-smoke.cjs" "$SNAP" "$OUT/smoke-cjs-$V.json"
done

# 3. React install matrix
for N in $NODES; do
  V=$("$N/node" --version)
  for CASE in none react17 react18 react19 existing17; do
    D="$OUT/work/matrix-$CASE-$V"
    case $CASE in
      none) step "matrix-install-$CASE-$V" consumer "$D" "$N" "$TARBALL" ;;
      react17) step "matrix-install-$CASE-$V" consumer "$D" "$N" "$TARBALL" react@17.0.2 react-dom@17.0.2 ;;
      react18) step "matrix-install-$CASE-$V" consumer "$D" "$N" "$TARBALL" react@18.3.1 react-dom@18.3.1 ;;
      react19) step "matrix-install-$CASE-$V" consumer "$D" "$N" "$TARBALL" react@19.1.0 react-dom@19.1.0 ;;
      existing17)
        step "matrix-tree-$CASE-$V" consumer "$D" "$N" react@17.0.2 react-dom@17.0.2 openai@4.104.0
        step "matrix-install-$CASE-$V" bash -c "cd '$D' && PATH='$N':\$PATH npm install --ignore-scripts --no-audit --no-fund '$TARBALL'" ;;
    esac
    FLAG=""; [ "$CASE" = none ] && FLAG="--no-react"
    for F in esm cjs; do
      EXT=mjs; [ $F = cjs ] && EXT=cjs
      step "matrix-run-$CASE-$F-$V" bash -c "cd '$D' && '$N/node' smoke.$EXT > '$OUT/matrix-$CASE-$F-$V.json'; true"
      step "matrix-check-$CASE-$F-$V" node "$C/check-smoke.cjs" "$SNAP" "$OUT/matrix-$CASE-$F-$V.json" $FLAG
    done
  done
done

# 4. tsc fixtures (first Node)
D="$OUT/work/tsc"
step tsc-install consumer "$D" "$FIRST" "$TARBALL" react@18.3.1 "typescript@$TSC_VERSION" "@types/react@$TYPES_REACT" "@types/node@$TYPES_NODE"
cp "$C/tsc/"* "$D/"
cp "$D/consumer.ts" "$D/consumer.mts"; cp "$D/consumer.ts" "$D/consumer.cts"
for CFG in node10 node10-root node16 bundler; do
  step "tsc-$CFG" bash -c "cd '$D' && '$FIRST/node' node_modules/typescript/bin/tsc -p tsconfig.$CFG.json"
done

# 5. esbuild metafiles (first Node, the toolchain's esbuild)
ESBUILD="$GC/node_modules/.bin/esbuild"
for E in gateway react nextjs; do
  step "esbuild-$E" bash -c "cd '$D' && '$ESBUILD' entry-$E.mjs --bundle --platform=browser --format=esm --external:react --metafile='$OUT/meta-$E.json' --outfile='$OUT/work/bundle-$E.js' --log-level=warning"
  step "metafile-$E" node "$C/check-metafile.cjs" "$OUT/meta-$E.json" "entry-$E.mjs"
done

# 6. D-18 in real browsers: Chromium, Firefox and WebKit through Playwright
#    (GW_PLAYWRIGHT = the path of an installed playwright module; it finds
#    its browsers through PLAYWRIGHT_BROWSERS_PATH, as Playwright always does).
if [ -n "${GW_PLAYWRIGHT:-}" ]; then
  cp "$GC/scripts/browser/d18-entry.mjs" "$D/"
  step esbuild-d18 bash -c "cd '$D' && '$ESBUILD' d18-entry.mjs --bundle --platform=browser --format=esm --metafile='$OUT/meta-d18.json' --outfile='$OUT/work/bundle-d18.js' --log-level=warning"
  step browsers-d18 bash -c "PLAYWRIGHT_MODULE='$GW_PLAYWRIGHT' '$LAST/node' '$GC/scripts/browser/d18-browser.cjs' '$OUT/work/bundle-d18.js' '$OUT/browsers-d18.json'"
fi

# 7. No install may resolve a peer conflict by overriding it: npm can print
#    "npm warn ERESOLVE overriding peer dependency" and still exit 0, so every
#    install log is read and any ERESOLVE line fails this step.
step eresolve node "$C/check-install-logs.cjs" "$OUT"

{ for N in $NODES; do "$N/node" --version; PATH="$N:$PATH" npm --version; done; } > "$OUT/env.txt" 2>&1
rm -rf "$OUT/work"
exit $fails
