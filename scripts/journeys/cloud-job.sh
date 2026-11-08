#!/usr/bin/env bash
# Preserve the true command status; infrastructure receives only zero or one.
set -uo pipefail
repo=$1
inputs=$2
mkdir -p "$repo/out"
run() {
  bash "$repo/scripts/journeys/regression-job.sh" "$repo" || return 1
  bash "$repo/scripts/journeys/semantic-job.sh" "$repo" "$inputs" || return 1
  python3 -I "$repo/scripts/journeys/run.py" --emit-legs "$repo/out/J24-LEGS.json" || return 1
  local wheel tarball
  wheel=$(find "$inputs" -maxdepth 1 -name '*.whl' -print -quit)
  tarball=$(find "$inputs" -maxdepth 1 -name '*.tgz' -print -quit)
  local c0=0 config=0
  python3 -I "$repo/scripts/journeys/run.py" --manifest "$inputs/manifest-entry.json" \
    --wheel "$wheel" --tarball "$tarball" --policy "$repo/scripts/journeys/historical-policy.json" \
    --binding "$repo/scripts/journeys/stub-binding.json" --out "$repo/out/c0" --cells N00 \
    2>&1 | tee "$repo/out/c0.log" || c0=$?
  python3 -I "$repo/scripts/journeys/run.py" --manifest "$inputs/manifest-entry.json" \
    --wheel "$wheel" --tarball "$tarball" --policy "$repo/scripts/journeys/historical-policy.json" \
    --binding "$repo/scripts/journeys/stub-binding.json" --out "$repo/out/config" --cells N01 \
    2>&1 | tee "$repo/out/config.log" || config=$?
  printf 'c0=%s\nconfig=%s\n' "$c0" "$config" > "$repo/out/probe-exits.txt"
  [ "$c0" -eq 0 ] && [ "$config" -eq 0 ]
}
run
rc=$?
printf '%s\n' "$rc" > "$repo/out/command-exit.txt"
if [ "$rc" -eq 0 ]; then exit 0; else exit 1; fi
