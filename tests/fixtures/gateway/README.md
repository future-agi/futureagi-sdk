# AgentCC parity goldens

These fixtures pin what the published AgentCC SDKs do, so the port into this SDK
(`fi.gateway`, `@future-agi/sdk/gateway`) and the 2.0 compatibility shims can be
compared against them call by call. A golden is a recording of the case catalog
against one released artifact: every request the SDK sends (method, URL, query,
headers, body or multipart parts, timeout) and everything the caller sees
(return values, parsed models, metadata, raised errors with their class chain,
`str`, `repr`, args and pickle round trip, stream items, retry sleeps, logs and
warnings).

## Layout

| Path | What it is |
|---|---|
| `golden/<target>/<area>.json` | one golden per target, one file per catalog area |
| `golden/<target>/index.json` | the recording environment, every case id, each area file's sha256; for TypeScript also the export keys of every subpath under `import()` or `require()` and the normalised `.d.ts` surface |
| `golden/MANIFEST.json` | sha256 of every golden file and the result of the twice-recorded identity check |
| `catalog.json` | the case catalog: each bullet, the case-id prefixes that cover it, required items per golden |
| `intended-differences.json` | every allowed difference (D-01 ... D-21) with the comparisons it applies to, its match rules and its status |
| `responses.json`, `stream-cases-extra.json`, `sse-malformed.json` | canned gateway answers shared by both recorders |
| `stream-error-frames.json` | unchanged gateway stream-error payloads from `stream-fixture-source`; the public metadata projection and the wire cases each have an independent SHA256 integrity check |
| `comparator-cases.json` | conformance cases both comparators must pass |
| `hygiene-cases.json` | conformance cases both local-path guards must pass |
| `e-old/` | how the goldens were made: artifact hashes, the registry projection, the pinned installs and the scripts |

## Targets (E-OLD)

| Golden | Artifact | Hash checked against the registry |
|---|---|---|
| `py-agentcc-1.0.0` | PyPI `agentcc` 1.0.0 wheel | sha256 `2eb341ee1ad626e663d6bb875a44145c425ea84d457d0e85dab1c1cd18fea803` |
| `ts-client-1.0.0-esm`, `-cjs` | npm `@agentcc/client` 1.0.0 | shasum `81b5315b2c79c14d9dd6c1e49a82997c5944745e` |
| `ts-client-1.0.1-esm`, `-cjs` | `@agentcc/client` 1.0.1, packed from agent-command-center-sdk client-patch-source (unpublished) | the lock pins the packed tarball's integrity |
| `ts-integrations-1.0.0-esm`, `-cjs` | npm `@agentcc/{client,langchain,llamaindex,react,vercel}` 1.0.0 | every tarball's shasum and integrity |

`e-old/artifacts.json` holds each computed hash beside the registry's own value
for that exact version (`npm view <name>@1.0.0 dist`, not `dist-tags.latest`,
which moves when a newer version is published), with npm pack's report as a
separate second check, and `hash_check` lists every problem found (none).
It also shows that the wheel's 70 files equal `sdk/python/src/agentcc` at
release-source, and compares each published npm tarball file by file with a build of
release-source:

- `@agentcc/client`, `@agentcc/langchain`, `@agentcc/llamaindex` and
  `@agentcc/vercel`: only `README.md` and `package.json` differ, the two
  files that are not build output.
- `@agentcc/react`: `README.md`, `package.json`, `dist/provider.d.ts` and
  `dist/provider.d.ts.map` differ, so its published type declarations are not
  a release-source build. The published `provider.d.ts` declares `AgentCCProvider`'s
  return type as `import("react/jsx-runtime").JSX.Element` where the build
  declares `import("react").JSX.Element`, and the source map differs with it.
  Every JavaScript file is identical.

For every other file that differs, `published_vs_release_source_build` keeps the
unified diff (published side first). `e-old/registry-npm.json` is the registry
projection for every name checked: the five `@agentcc/*` packages are all
published (0.1.0 on 2026-04-09, 1.0.0 on 2026-04-22), `@futureagi/agentcc`, the
name some documentation uses, returns E404, and the unscoped npm name `agentcc`
(listed by the text search) is an unrelated package ("agent cost control",
0.1.7 to 0.1.81, first published 2026-07-08), so `npm i agentcc` does not install
Future AGI code. The `scope:agentcc` search
returns nothing, so publication was checked name by name.

Under `require()` (Node 22.23), `@agentcc/client` 1.0.0 fails to load ("exports
is not defined in ES module scope"), so `ts-client-1.0.0-cjs` records the load
failure and no case. The four integration packages are ES modules only
(`"type": "module"`); Node 22 loads them through `require()` and they import the
client's ES build, so the langchain, llamaindex and vercel cases run under
`require()` too, while a CommonJS caller cannot construct the client the React
provider needs (`ts-integrations-1.0.0-cjs`). Older Node lines without
`require()` of ES modules would fail earlier; that Node 18 / 20 / 22 matrix
belongs to the TypeScript port's packed-tarball smoke.

## Public provenance

Historical source revisions are represented by named records, not links to
unpublished commits. `review-records.json` retains the existing independent
review verdicts and binds each one to the exact comparison rules it reviewed.
Both language validators reject changed records or broadened rules; the
projection does not grant any new acceptance. Golden recordings are unchanged.

`scripts/gateway/project_public_metadata.py` regenerates public fixture metadata
from retained originals and an explicit source-name mapping. It rejects changes
to comparison rules, statuses, case names or wire payloads, including accidental
replacement of a revision-like prefix inside a content digest. The original
source mapping stays with the retained evidence, outside the public tree.

## Recording

`e-old/record-e-old.sh <out> <work> <src-client-patch-source> <src-release-source>` runs on a
disposable Linux host (Python 3.12, uv, Node 22, npm 10). It downloads the
artifacts, checks every hash, installs each target from the pinned files
(`e-old/constraints-py.txt`; `npm ci` from `e-old/npm/*/package-lock.json`),
records every target twice in fresh processes and compares the two runs with
`cmp`. Run 2 records from a copy of the recorders at another checkout path,
with the npm installs copied and the venv built again elsewhere, so the
identity also shows that no golden depends on where it was recorded.
`e-old/install_goldens.py` copies run 1 here and writes the manifest; it
refuses if any file differs. The sources are `git archive <sha> sdk` exports of
agent-command-center-sdk.

A golden never holds a local path. The TypeScript recorder replaces a stack
frame's whole location, line and column included, with `<frame>` (React prints
a component stack when a hook runs outside its provider) and an install path up
to `node_modules/` with `<path>/node_modules/`; the Python recorder replaces an
install path up to `site-packages/` with `<path>/` and has no frame rule, since
no Python case records a frame. Both then refuse to write any file that still
carries a local path (`_hygiene.py`, `harness/hygiene.mjs`): a `file://` URL, an
absolute path under a home, volume or temp root, or one of the recorder's own
directories (checkout, install, venv, working, home, temp and output
directories). `test_parity_hygiene.py` and `hygiene.test.mjs` scan every
committed golden with the same rule.

The recorders replace the transport (httpx's transports in Python, `fetch` in
TypeScript) for each case and refuse sockets, so nothing reaches a network.
Time, sleeps, timers, randomness and UUIDs are fixed per case; `PYTHONHASHSEED`
is not pinned, so two identical runs also show that no set or dict order leaks.

## Comparing a new implementation

```
cd python/tests/gateway
python -m parity.record --root fi.gateway --out /tmp/e-new        # pip install -c tests/fixtures/gateway/e-old/constraints-py.txt first
python -m parity.compare --golden ../../../tests/fixtures/gateway/golden/py-agentcc-1.0.0 --new /tmp/e-new --label 'py-agentcc-1.0.0->e-new-py'
```

TypeScript: `node typescript/futureagi/gateway-client/tests/parity/record.mjs
--install <dir with node_modules> --target client --format esm --out <dir>`, then
`compare.mjs` with the same arguments.

The label names the comparison, and both comparators refuse (exit 2) a label
that does not fit its two directories (`labels.py`, `labels.mjs`): its golden
side must be the committed golden passed as `--golden`, byte for byte; its new
side is either a golden, and then `--new` must be that golden byte for byte (a
fresh re-recording is), or a new recording named in `catalog.json`
`comparisons`, judged only against a baseline listed there for it.

The rules:

- **Only a `proven` entry covers a difference.** It carries evidence, a test id
  and a reviewer record (who reviewed it, the reviewed revision or a named
  retained review record, and the verdict). The four Python transport-fix
  entries use `record: python-transport-fixes-2026-10-28`, with an ISO review
  date and a repository-relative regression-test path in `evidence`. The
  exact reviewed revision and authoritative review evidence are retained
  privately under that record; the test path is reproducible coverage, not
  the review transcript. No unpublished revision identifier belongs in these
  public records, and a public PR revision must not be substituted for the
  actual reviewed revision. Both shared and Python overlay checks validate
  this schema; legacy commit-based signatures keep their existing checks.
  A difference no proven entry covers fails, and a proven entry that applies
  but covers nothing fails.
- **A `planned` entry covers nothing.** It is a work-list item; the report
  names it beside each unlisted difference it would match. When the delta
  lands, its port narrows the entry's rules, sets it to `proven` and fills in
  the evidence, test id and reviewer.
- **A proven rule that can judge a new recording is pinned:** an exact path, or
  an `old` / `new` regex on the value that pins it. A bare glob over a case or
  a subtree is refused, and so is a regex that matches arbitrary text (`.*`,
  `x?`, an empty pattern), since the comparators apply it with `re.search`
  (`test_parity_intended.py`).
- **Baselines.** A new Python recording is compared with `py-agentcc-1.0.0`. A
  new TypeScript client recording is compared with `ts-client-1.0.1-*`. The
  1.0.0 to 1.0.1 step is D-01, proven once between the two fixed goldens, so it
  never covers a difference in a port. Integrations are compared with
  `ts-integrations-1.0.0-*`.

`python/tests/gateway/parity/test_parity_enew.py` runs the Python comparison
once `fi.gateway` exists. It runs only in the environment the golden was
recorded in: Python 3.12 and the library versions in `index.json`, installed
with `-c e-old/constraints-py.txt`. In any other environment it is skipped, and
the skip reason names each difference. The fixed CI install line resolves the
newest pydantic, whose error text and `errors.pydantic.dev/<version>` links
differ from the golden's, so in CI the test is a named skip, not a pass.

**Twins.** The env rules (D-07 and D-14: key and base-URL resolution) hold in both
languages, so both recorders run the env matrix under the same ids with the
same values: 7 key sources by 8 base-URL sources, 9 URL shapes, `FI_*` /
`OPENAI_*` isolation, the `FI_API_KEY` and `FI_SECRET_KEY` guard cases, and the
import-time `AGENTCC_GATEWAY_URL` constant, read in a fresh process per case.
`test_parity_twins.py` (in the CI line) compares the ids of the Python golden
with every TypeScript client golden and fails on a gap, apart from the
language-only prefixes in `catalog.json` `twins` (`env.async.*`, the async
client). `compare.test.mjs` checks every TypeScript golden against its case
code, as `test_python_golden_is_current_with_the_catalog_code` does for Python.

`golden/MANIFEST.json` records the recorder's own cmp of its two runs. The
independent check is to re-run `record-e-old.sh` on a fresh host and compare
the result with these files using `diff -r`.

## Behaviour the goldens pin that the port must decide on

Recorded facts about the 1.x releases, beyond the planned deltas:

1. **Python, audio uploads.** `audio.transcriptions.create` and
   `audio.translations.create` put `file` in a JSON body, so bytes or a
   `(name, bytes, type)` tuple raise `TypeError` before any request is sent
   (`resource.audio.transcriptions.*`).
2. **Python, cache-hit streams.** A JSON answer to `stream=True` raises
   `httpx.ResponseNotRead` from the sync client; the async client yields one
   chunk (`stream.extra.cache_hit_json_to_stream.*`).
3. **Python, embeddings.** `EmbeddingResponse` requires `usage.completion_tokens`,
   so an OpenAI-shaped embedding answer fails validation; with
   `completion_tokens: 0` it parses (`resource.embeddings.*`).
4. **Python, rerank.** A result's `document` must be a string; `{"text": ...}`
   fails validation (`resource.rerank.*`).
5. **Python, `create_mock_client`.** It does not mock anything: requests go to
   `https://mock.agentcc.test` (`mock.create_mock_client`).
6. **TypeScript, `@agentcc/vercel` 1.0.0.** With no base URL it calls
   `https://api.agentcc.ai/v1`, and with only `AGENTCC_API_KEY` set it sends that
   key there (`integration.vercel.defaults`, `integration.vercel.key_env_only`).
7. **TypeScript, 1.0.0 version.** The published 1.0.0 reports version `0.1.0` in
   `VERSION`, `User-Agent` and `x-agentcc-sdk-version` (fixed in 1.0.1, D-01c).
8. **TypeScript, a late stream error.** In 1.0.0 and 1.0.1 a consumer that
   stops at the `done` event never sees an error frame sent after the finish and
   usage chunks; Python raises before `done`
   (`stream.extra.late_error_after_finish_reason.break_on_done`, D-16).
9. **Python, a closed client.** `close()` / `aclose()` drop the httpx client,
   and the next request builds a new one, so a closed client sends that request
   and succeeds (`resource.close`). An injected `http_client` is never closed by
   the SDK (`resource.http_client`).
10. **Both, an empty argument falls through.** 1.x resolves the key and the base
    URL with `||` (TypeScript) and `or` (Python), so `apiKey: ""` /
    `api_key=""` sends the `AGENTCC_API_KEY` value, and an empty base URL uses
    `AGENTCC_BASE_URL` (`env.key_empty_arg_env.*`, `env.*.url_empty_arg_env`).
    A port that writes `??` or `is None` changes this, so the port decides.
11. **Both, `FI_GATEWAY_*` is never read.** With `AGENTCC_*` and `FI_GATEWAY_*`
    both set, 1.x sends the `AGENTCC_*` value with no warning; with only
    `FI_GATEWAY_*` set it behaves as if nothing were set (no key in TypeScript,
    an `AgentCCError` in Python). D-14 reverses the order (`FI_GATEWAY_*` wins,
    with one log line or `console.warn`), so `env.*both_env_differ*` and
    `env.*fi_gateway_env*` are the D-14 baseline.
12. **TypeScript, the 1.0.1 client ignores `AGENTCC_GATEWAY_URL`.** The client
    reads `baseUrl`, then `AGENTCC_BASE_URL`, then `http://localhost:8090`
    (`env.key_arg.url_gateway_url_env` sends to localhost:8090). Only the
    exported `AGENTCC_GATEWAY_URL` constant reads that variable, once at
    import: `AGENTCC_GATEWAY_URL`, then `AGENTCC_BASE_URL`, then
    `https://gateway.futureagi.com/v1` (`env.gateway_url_constant.*`; Python's
    constant reads only `AGENTCC_BASE_URL`). A TypeScript client that read
    `AGENTCC_GATEWAY_URL` after `AGENTCC_BASE_URL` would have a new
    behaviour, not the 1.0 read order.
13. **Both, the base URL is used as given.** Only a trailing slash is
    dropped, so `/v1` gives `/v1/v1/...`, `/v1/v1` gives `/v1/v1/v1/...`,
    `/gw/v1` gives `/gw/v1/v1/...` and `/V1` gives `/V1/v1/...`
    (`env.base_url.*`; D-07 strips one `/v1`).
14. **Both, no FI-key guard.** A gateway key equal to `FI_API_KEY` or
    `FI_SECRET_KEY` is sent as the Bearer token
    (`env.fi_api_key_reused_as_gateway_key`, `env.fi_secret_key_reused_as_gateway_key`;
    D-14 adds the guard).
15. **Python, the legacy pydantic `agentcc.config` models** (S bucket, kept by
    the shim). Their `to_headers()` differs from the dataclass `GatewayConfig`:
    a disabled cache sends `x-agentcc-cache-enabled: false`, `ttl` stays a
    string, and every section, the cache included, goes into one
    `x-agentcc-config`; the client sends that when given one as `config=`
    (`config.legacy_pydantic.*`).
