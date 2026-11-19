#!/usr/bin/env bash
# Preserve command statuses while returning only zero or one to infrastructure.
set -uo pipefail
repo=$1
inputs=$2
mode=${3:-check}
mkdir -p "$repo/out"
run() {
  local wheel tarball code overall=0
  wheel=$(find "$inputs" -maxdepth 1 -name '*.whl' -print -quit)
  tarball=$(find "$inputs" -maxdepth 1 -name '*.tgz' -print -quit)
  local snapshot=()
  if [ "$mode" = derive ]; then
    python3 -I "$repo/scripts/journeys/ts_inventory.py" "$tarball" --write "$repo/out/typescript-inventory.json" || return 1
    snapshot=("$repo/out/typescript-inventory.json")
  fi
  python3 -I "$repo/scripts/journeys/test_emitted_absence.py" "$tarball" "${snapshot[@]}" > "$repo/out/emitted-absence.log" 2>&1
  code=$?; printf 'emitted-absence=%s\n' "$code" >> "$repo/out/semantic-exits.txt"
  [ "$code" -eq 0 ] || overall=1
  python3 -I "$repo/scripts/journeys/test_retained_tarball.py" "$tarball" "$repo/out/retained-controls" > "$repo/out/retained-controls.log" 2>&1
  code=$?; printf 'retained-controls=%s\n' "$code" >> "$repo/out/semantic-exits.txt"
  [ "$code" -eq 0 ] || overall=1
  python3 -I "$repo/scripts/journeys/test_cli_entrypoint.py" "$wheel" "$repo/out/cli-controls" > "$repo/out/cli-controls.log" 2>&1
  code=$?; printf 'cli-controls=%s\n' "$code" >> "$repo/out/semantic-exits.txt"
  [ "$code" -eq 0 ] || overall=1
  return "$overall"
}
run
rc=$?
printf '%s\n' "$rc" > "$repo/out/command-exit.txt"
if [ "$rc" -eq 0 ]; then exit 0; else exit 1; fi
