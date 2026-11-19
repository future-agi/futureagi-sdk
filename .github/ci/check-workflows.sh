#!/usr/bin/env bash
# Fast, offline workflow checks. Requires Python with requirements.txt installed
# and actionlint v1.7.7 on PATH. Run from any working directory.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3 .github/ci/workflow_policy.py
python3 -m unittest discover -s .github/ci -p 'test_workflow_policy*.py' -v
shopt -s nullglob
workflows=(.github/workflows/*.yml .github/workflows/*.yaml)
# actionlint handles YAML, expressions and workflow schemas; the language
# linters are separate jobs, so these optional integrations stay disabled.
actionlint -shellcheck= -pyflakes= "${workflows[@]}"
