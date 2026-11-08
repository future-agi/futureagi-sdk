#!/usr/bin/env bash
# E-OLD artifacts for the AgentCC parity goldens.
#
# Runs on a disposable Linux VM only (never on a workstation): it downloads from PyPI and
# npm, builds two git trees with npm, and packs tarballs. Registry reads are
# credential-free: an empty npm user config and no pip config.
#
# Usage: fetch-artifacts.sh <out-dir> <work-dir> <src-client-patch-source> <src-release-source>
#   <out-dir>   text evidence only (hashes, registry JSON, logs); safe to pull
#   <work-dir>  wheel, tarballs, builds; stays on the VM
#   <src-*>     `git archive <sha> sdk` exports of agent-command-center-sdk
#
# Writes <out-dir>/raw/* (registry answers as received), <out-dir>/*.sha* and
# the build logs. summarize_artifacts.py turns them into artifacts.json.
set -euo pipefail

OUT=${1:?out dir}
WORK=${2:?work dir}
SRC05=${3:?client-patch-source export}
SRC98=${4:?release-source export}

mkdir -p "$OUT/raw" "$OUT/logs" "$WORK"
: > "$WORK/empty-npmrc"
export npm_config_userconfig="$WORK/empty-npmrc"
export npm_config_cache="$WORK/npm-cache"
export npm_config_audit=false npm_config_fund=false npm_config_update_notifier=false
export npm_config_registry=https://registry.npmjs.org/
export PIP_CONFIG_FILE=/dev/null PIP_NO_INPUT=1 PIP_DISABLE_PIP_VERSION_CHECK=1

PY=/usr/bin/python3.12
{ echo "node $(node --version)"; echo "npm $(npm --version)"; echo "$($PY --version)"; echo "uv $(uv --version)"; uname -srm; } > "$OUT/tools.txt"

# --- PyPI: agentcc 1.0.0 wheel --------------------------------------------
uv venv "$WORK/venv-dl" --python "$PY" --seed -q
"$WORK/venv-dl/bin/pip" download 'agentcc==1.0.0' --no-deps --only-binary=:all: \
  -d "$WORK/pypi" > "$OUT/logs/pip-download.log" 2>&1
(cd "$WORK/pypi" && sha256sum ./*.whl) > "$OUT/pypi-wheel.sha256"
curl -fsS https://pypi.org/pypi/agentcc/1.0.0/json > "$OUT/raw/pypi-agentcc-1.0.0.json"
curl -fsS https://pypi.org/pypi/agentcc/json > "$OUT/raw/pypi-agentcc.json"
mkdir -p "$WORK/wheel-x"
"$PY" -I -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' \
  "$(ls "$WORK"/pypi/*.whl)" "$WORK/wheel-x"

# --- npm: the published tarballs --------------------------------------------
mkdir -p "$WORK/npm-published"
(cd "$WORK/npm-published" && npm pack @agentcc/client@1.0.0 @agentcc/langchain@1.0.0 \
  @agentcc/vercel@1.0.0 @agentcc/react@1.0.0 @agentcc/llamaindex@1.0.0 --json \
  > "$OUT/raw/npm-pack-published.json" 2> "$OUT/logs/npm-pack-published.log")
(cd "$WORK/npm-published" && sha1sum ./*.tgz && for f in ./*.tgz; do
  printf 'sha512-%s  %s\n' "$(openssl dgst -sha512 -binary "$f" | base64 -w0)" "$f"; done) > "$OUT/npm-published.sums"

# --- npm: what the registry lists for the scope ------------------------------
npm search --json --searchlimit=100 'scope:agentcc' > "$OUT/raw/npm-search-scope-agentcc.json" \
  2> "$OUT/logs/npm-search.log" || echo "npm search exit=$?" >> "$OUT/logs/npm-search.log"
npm search --json --searchlimit=100 'agentcc' > "$OUT/raw/npm-search-text-agentcc.json" \
  2>> "$OUT/logs/npm-search.log" || echo "npm search (text) exit=$?" >> "$OUT/logs/npm-search.log"
NAMES=$("$PY" -I -c 'import json,sys
names = {"@agentcc/client","@agentcc/langchain","@agentcc/llamaindex","@agentcc/react","@agentcc/vercel","@futureagi/agentcc"}
try:
    for f in sys.argv[1:]:
        names |= {p["name"] for p in json.load(open(f)) if p["name"].startswith("@agentcc/") or p["name"] == "agentcc"}
except Exception:
    pass
print("\n".join(sorted(names)))' "$OUT/raw/npm-search-scope-agentcc.json" "$OUT/raw/npm-search-text-agentcc.json")
: > "$OUT/npm-view-exit.txt"
for pkg in $NAMES; do
  safe=${pkg//\//__}
  set +e
  npm view "$pkg" --json > "$OUT/raw/npm-view-$safe.json" 2> "$OUT/logs/npm-view-$safe.log"
  echo "$pkg $?" >> "$OUT/npm-view-exit.txt"
  set -e
done
# The registry's dist for each exact version packed above (dist-tags.latest moves
# when a newer version is published; summarize_artifacts.py checks against these).
: > "$OUT/npm-view-dist-exit.txt"
for spec in @agentcc/client@1.0.0 @agentcc/langchain@1.0.0 @agentcc/vercel@1.0.0 \
  @agentcc/react@1.0.0 @agentcc/llamaindex@1.0.0; do
  safe=${spec//\//__}
  set +e
  npm view "$spec" dist --json > "$OUT/raw/npm-view-dist-$safe.json" 2> "$OUT/logs/npm-view-dist-$safe.log"
  echo "$spec $?" >> "$OUT/npm-view-dist-exit.txt"
  set -e
done

# --- builds: @agentcc/client 1.0.1 from client-patch-source -----------------------------
build_client() {  # <src-export> <dest> <tag>
  cp -R "$1/sdk/typescript" "$2"
  (cd "$2" && npm ci > "$OUT/logs/npm-ci-client-$3.log" 2>&1 \
    && npm run build > "$OUT/logs/build-client-$3.log" 2>&1 \
    && npm pack --json > "$OUT/raw/npm-pack-client-$3.json" 2> "$OUT/logs/pack-client-$3.log")
}
build_client "$SRC05" "$WORK/b05" client-patch-source
build_client "$SRC98" "$WORK/b98" release-source

# --- builds: the four integration packages at release-source -----------------------
for p in agentcc-react agentcc-llamaindex agentcc-langchain agentcc-vercel; do
  d="$WORK/b98/packages/$p"
  if [ -f "$d/package-lock.json" ]; then inst="npm ci"; else inst="npm install --no-package-lock"; fi
  (cd "$d" && $inst > "$OUT/logs/install-$p.log" 2>&1 \
    && npm ls --all --json > "$OUT/raw/npm-ls-$p.json" 2>/dev/null; \
    npm run build > "$OUT/logs/build-$p.log" 2>&1 \
    && npm pack --json > "$OUT/raw/npm-pack-$p-release-source.json" 2> "$OUT/logs/pack-$p.log")
done

# --- collect every tarball in one place, with sums --------------------------
mkdir -p "$WORK/tarballs"
cp "$WORK"/npm-published/*.tgz "$WORK/tarballs/"
mkdir -p "$WORK/tarballs/local-client-patch-source" "$WORK/tarballs/local-release-source"
cp "$WORK"/b05/*.tgz "$WORK/tarballs/local-client-patch-source/"
cp "$WORK"/b98/*.tgz "$WORK/tarballs/local-release-source/"
cp "$WORK"/b98/packages/*/*.tgz "$WORK/tarballs/local-release-source/"
(cd "$WORK/tarballs" && find . -name '*.tgz' | sort | while read -r f; do
  printf '%s  %s  sha512-%s\n' "$(sha1sum "$f" | cut -d' ' -f1)" "$f" \
    "$(openssl dgst -sha512 -binary "$f" | base64 -w0)"; done) > "$OUT/tarballs.sums"

# --- unpack every tarball for the file-by-file comparison ---------------------
mkdir -p "$WORK/unpacked"
(cd "$WORK/tarballs" && find . -name '*.tgz' | sort | while read -r f; do
  d="$WORK/unpacked/${f#./}"; d=${d%.tgz}; mkdir -p "$d"; tar -xzf "$f" -C "$d"; done)
echo "fetch-artifacts: done"
