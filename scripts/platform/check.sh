#!/usr/bin/env bash
# Every platform codegen gate. Run on the build worker, not a developer laptop.
# The whole committed tree is checked first and must have zero findings. There is no debt
# baseline or environment-variable bypass in fast checks. hygiene-tree.mjs HEAD --findings <file>
# writes the strict findings list for review without changing the pass criterion.
#
#   scripts/platform/check.sh [--input <customer-openapi.json>]
#
# 1. content pin: the scoped spec hashes to source.json's scoped.sha256, and both generated policy
#    modules carry that hash; with --input, the input must match source_digest and re-scoping it must
#    reproduce the committed scoped spec byte for byte;
# 2. regenerate-and-diff: scripts/generate-platform-sdk.sh --out <tmp> (hey-api, the policy emitter,
#    the Python types, black) and scripts/platform/unasync.py --out <tmp> must equal the committed files;
# 3. wrapper-map rules (with --input, also: every pinned operation is wrapped or has a reason);
# 4. the hygiene scan, in both languages (with HYGIENE_NAMES=<file>, also: the plain list of internal
# names, kept outside this repository, agrees with the hashed ones in hygiene-rules.json, both ways);
# 5. the lints (module size, no URL paths, TSDoc); 6. the tooling's own tests,
# the conformance kit's validate.mjs and its tests (set SDKCONF_PYTHON to a Python with httpx to run the
# py shell tests too); 7. the policy counts of the scoped spec.
# Needs Node 18+, python3 (3.10+), npx and uvx (for the pinned generators).
#
# Before a branch is pushed to the public repository, also scan its commit messages (a message cannot be
# fixed once it is public): node scripts/platform/hygiene-scan.mjs --commits <base>..HEAD
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
INPUT=""
if [[ $# -eq 2 && "$1" == "--input" ]]; then
  INPUT="$2"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--input <customer-openapi.json>]" >&2
  exit 2
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SCOPED="openapi/platform/generated/futureagi-platform.openapi.json"
step() { printf '\n== %s\n' "$1"; }

step "0. whole-tree hygiene (strict: zero hits)"
node scripts/platform/hygiene-tree.mjs HEAD

step "1. sha pin"
node -e '
const c = require("node:crypto"), f = require("node:fs");
const [scoped] = process.argv.slice(1);
const source = JSON.parse(f.readFileSync("openapi/platform/source.json", "utf8"));
const got = c.createHash("sha256").update(f.readFileSync(scoped)).digest("hex");
const fail = (m) => { console.error("check: " + m); process.exit(1); };
if (got !== source.scoped.sha256) fail(`scoped spec sha256 ${got} != source.json scoped.sha256 ${source.scoped.sha256}`);
for (const file of ["python/fi/generated/platform/policy.py", "typescript/futureagi/src/generated/platform/policy.gen.ts"]) {
  const text = f.readFileSync(file, "utf8");
  if (!text.includes(got) || !text.includes(source.source_digest)) fail(`${file} does not carry the pinned and scoped content digests`);
}
if (!/^sha256:[a-f0-9]{64}$/.test(source.source_digest)) fail("invalid source content digest");
console.log(`scoped ${got}; source ${source.source_digest}`);
' "$SCOPED"
if [[ -n "$INPUT" ]]; then
  cp "$INPUT" "$TMP/contract.json"
  node scripts/platform/source-pin.mjs verify openapi/platform/source.json "$TMP/contract.json"
  node scripts/platform/scope-filter.mjs "$TMP/contract.json" "$TMP/scoped.json" "$TMP/operations.txt" >/dev/null
  cmp "$TMP/scoped.json" "$SCOPED"
  cmp "$TMP/operations.txt" openapi/platform/generated/futureagi-platform.operations.txt
  echo "re-scoping the pinned file reproduces the committed scoped spec"
fi

step "2. regenerate and diff"
scripts/generate-platform-sdk.sh --out "$TMP/regen" >/dev/null
# Catalog namespaces share the Python platform output directory; regenerate both
# owners before comparing it, and check the TypeScript catalog slice as well.
python3 scripts/generate-catalog-namespaces.py --out "$TMP/regen"
# Observe shares the generated Python platform directory with the catalog.
python3 scripts/generate-tracing.py --out "$TMP/regen"
python3 scripts/generate-tracing.py --check
python3 scripts/licensed_operation_docs.py --check
# Management owns another slice of the same Python directory.
python3 scripts/fa-management/generate.py --out "$TMP/regen"
python3 scripts/fa-management/generate.py --check
diff -r "$TMP/regen/typescript/futureagi/src/generated/fa-management" typescript/futureagi/src/generated/fa-management
node scripts/connectors/generate.mjs --out "$TMP/regen"
node scripts/connectors/generate.mjs --check
diff -r "$TMP/regen/typescript/futureagi/src/generated/connectors" typescript/futureagi/src/generated/connectors
if [[ -f scripts/platform/generate-console.py ]]; then
  for path in python/fi/agents/_async_client.py python/fi/agents/schedules/_async_client.py python/fi/environments/_async_client.py typescript/futureagi/src/agents/client.ts typescript/futureagi/src/agents/schedules/client.ts typescript/futureagi/src/environments/client.ts; do
    cmp "$TMP/regen/$path" "$path"
  done
fi
diff -r -x __pycache__ -x __tests__ "$TMP/regen/typescript/futureagi/src/generated/platform" typescript/futureagi/src/generated/platform
diff -r -x __pycache__ "$TMP/regen/typescript/futureagi/src/generated/catalog" typescript/futureagi/src/generated/catalog
diff -r -x __pycache__ "$TMP/regen/python/fi/generated/platform" python/fi/generated/platform
python3 scripts/platform/unasync.py --out "$TMP/unasync"
TWINS="$(python3 scripts/platform/unasync.py --list | sed 's/.* -> //')"
if [[ -n "$TWINS" ]]; then
  # shellcheck disable=SC2086
  uvx --python "${BLACK_PYTHON:-3.11}" --from "${BLACK_PACKAGE:-black==22.10.0}" black --quiet $(printf "$TMP/unasync/%s " $TWINS)
  while IFS= read -r twin; do cmp "$TMP/unasync/$twin" "$twin"; done <<< "$TWINS"
fi
echo "generated files are byte-identical to a fresh regeneration ($(printf '%s' "$TWINS" | grep -c . || true) sync twins)"

step "3. wrapper map"
if [[ -n "$INPUT" ]]; then
  python3 scripts/platform/wrapper_map.py --contract "$TMP/contract.json"
else
  python3 scripts/platform/wrapper_map.py
fi

step "3b. generated operation contracts and admission ledger"
python3 scripts/platform/contract_cases.py --check

step "4. hygiene"
node scripts/platform/hygiene-scan.mjs
python3 scripts/platform/hygiene_scan.py
if [[ -n "${HYGIENE_NAMES:-}" ]]; then
  node scripts/platform/hygiene-scan.mjs --names "$HYGIENE_NAMES"
else
  echo "hygiene: the internal-name list was not checked (set HYGIENE_NAMES=<file>)"
fi

step "5. lints"
node scripts/platform/lint/module-size.mjs
node scripts/platform/lint/no-url-paths.mjs
node scripts/platform/lint/tsdoc-coverage.mjs

step "6. tooling and conformance-kit tests"
node --test --test-concurrency=2 scripts/platform/test/*.test.mjs > "$TMP/tooling-tests.log" 2>&1 || { cat "$TMP/tooling-tests.log"; exit 1; }
grep -E '^# (tests|pass|fail)' "$TMP/tooling-tests.log"
node tests/platform-conformance/validate.mjs
KIT_TESTS=(tests/platform-conformance/test/*.test.mjs tests/platform-conformance/guards/no-prod-egress/test/*.test.mjs tests/platform-conformance/runners/test/shells.test.mjs)
node --test --test-concurrency=2 "${KIT_TESTS[@]}" > "$TMP/kit-tests.log" 2>&1 || { cat "$TMP/kit-tests.log"; exit 1; }
grep -E '^# (tests|pass|fail|skipped)' "$TMP/kit-tests.log"

step "7. policy counts"
node scripts/platform/pin-diff.mjs --counts "$SCOPED"

printf '\ncheck: OK\n'
