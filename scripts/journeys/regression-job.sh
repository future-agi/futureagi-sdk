#!/usr/bin/env bash
# Collect every regression exit; infrastructure sees only zero or one.
set -uo pipefail
repo=$1
mkdir -p "$repo/out"
run() {
  docker pull python:3.12-slim-bookworm || return 1
  docker pull node:22-bookworm-slim || return 1
  local overall=0 code file
  for file in test_matrix.py test_absence.py test_precedence.py; do
    docker run --rm --network none --cap-drop=ALL --security-opt=no-new-privileges \
      --mount "type=bind,source=$repo/scripts/journeys,target=/kit,readonly" \
      python:3.12-slim-bookworm python -I "/kit/$file" > "$repo/out/$file.log" 2>&1
    code=$?; printf '%s=%s\n' "$file" "$code" >> "$repo/out/regression-exits.txt"
    [ "$code" -eq 0 ] || overall=1
  done
  for file in test_network_node.cjs test_precedence_node.cjs; do
    docker run --rm --network none --cap-drop=ALL --security-opt=no-new-privileges \
      --mount "type=bind,source=$repo/scripts/journeys,target=/kit,readonly" \
      node:22-bookworm-slim node "/kit/$file" > "$repo/out/$file.log" 2>&1
    code=$?; printf '%s=%s\n' "$file" "$code" >> "$repo/out/regression-exits.txt"
    [ "$code" -eq 0 ] || overall=1
  done
  python3 -I "$repo/scripts/journeys/test_network_tree.py" "$repo/out/network-controls" > "$repo/out/network-controls.log" 2>&1
  code=$?; printf 'network-controls=%s\n' "$code" >> "$repo/out/regression-exits.txt"
  [ "$code" -eq 0 ] || overall=1
  return "$overall"
}
run > "$repo/out/regression-setup.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$repo/out/command-exit.txt"
if [ "$rc" -eq 0 ]; then exit 0; else exit 1; fi
