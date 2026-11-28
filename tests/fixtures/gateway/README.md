# AgentCC parity goldens

These fixtures record the behavior of the AgentCC SDKs for compatibility
comparisons. The Python parity tools compare `fi.gateway` with `agentcc` 1.0.0.
The TypeScript goldens document the AgentCC client and integrations. Each golden
records the case catalog against one target: the requests the SDK sends
(method, URL, query, headers, body or multipart parts, timeout) and what the
caller sees (return values, parsed models, metadata, raised errors with their
class chain, `str`, `repr`, args and pickle round trip, stream items, retry
sleeps, logs and warnings).

## Layout

| Path | What it is |
|---|---|
| `golden/<target>/<area>.json` | one golden per target, one file per catalog area |
| `golden/<target>/index.json` | the recording environment, every case id, each area file's sha256; for TypeScript also the export keys of every subpath under `import()` or `require()` and the normalised `.d.ts` surface |
| `golden/MANIFEST.json` | sha256 of every golden file and the result of the twice-recorded identity check |
| `catalog.json` | the case catalog: each bullet, the case-id prefixes that cover it, required items per golden |
| `intended-differences.json` | every allowed difference (D-01 ... D-21) with the comparisons it applies to, its match rules and its status |
| `responses.json`, `stream-cases-extra.json`, `sse-malformed.json` | canned gateway responses used to record both sets of goldens |
| `stream-error-frames.json` | gateway stream-error payloads copied verbatim from `stream-fixture-source`; the public metadata projection and the wire cases each have an independent SHA256 integrity check |
| `comparator-cases.json` | comparator conformance cases |
| `hygiene-cases.json` | local-path guard conformance cases |
| `e-old/` | historical recipe and evidence: artifact hashes, the registry projection and pinned installs |

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
provider needs (`ts-integrations-1.0.0-cjs`). These recordings describe Node 22,
not Node releases that lack `require()` support for ES modules.

## Public provenance

Historical source revisions are represented by named records, not links to
unpublished commits. `review-records.json` retains the existing independent
review verdicts and binds each one to the exact comparison rules it reviewed.
The Python validator rejects changed records or broadened rules. The public
projection preserves the validation rules and the golden recordings.

`scripts/gateway/project_public_metadata.py` regenerates public fixture metadata
from retained originals and an explicit source-name mapping. It rejects changes
to comparison rules, statuses, case names or wire payloads, including accidental
replacement of a revision-like prefix inside a content digest. The original
source mapping stays with the retained evidence, outside the public tree.

## How the goldens were recorded

The historical recipe used a disposable Linux host with Python 3.12, uv,
Node 22 and npm 10. It downloaded and hashed the artifacts,
installed targets using `e-old/constraints-py.txt` and the npm lockfiles under
`e-old/npm/`, then recorded each target twice in fresh processes. The second
run used a different checkout path, copies of the npm installs and a separate
virtual environment. A byte-for-byte comparison checked that the recordings
did not depend on those paths. `e-old/install_goldens.py` copies the first run
and writes the manifest only if the runs match. The recipe used archived SDK
source trees and TypeScript recording tools that are not part of this checkout.
`e-old/record-e-old.sh` marks the entry point named in the manifest; it does
not run the combined recording here. The committed goldens and artifact
evidence can be inspected directly.

Golden recordings omit local paths. The TypeScript recorder replaced the
entire stack-frame location, including line and column, with `<frame>` and
replaced install paths through `node_modules/` with `<path>/node_modules/`.
The Python recorder replaces install paths through `site-packages/` with
`<path>/`; no Python case records a frame. Both guard against file URLs and
absolute paths under the recorder's directories, home, volume and temporary
roots. The Python suite's `test_parity_hygiene.py` scans the committed goldens
with the same local-path rules as the Python recorder.

The recorders substituted transport implementations (httpx's transports in
Python, `fetch` in TypeScript) and refused sockets. They controlled time,
sleeps, timers, randomness and UUIDs per case. With `PYTHONHASHSEED` unpinned,
matching runs also checked that set and dict iteration order did not affect
the recordings.

## Comparing the Python implementation

From the repository root, use Python 3.12 with `fi.gateway` installed and the
dependency versions from `e-old/constraints-py.txt`:

```sh
out=$(mktemp -d)
cd python/tests/gateway
python -m parity.record --root fi.gateway --out "$out"
python -m parity.compare \
  --golden ../../../tests/fixtures/gateway/golden/py-agentcc-1.0.0 \
  --new "$out" \
  --label 'py-agentcc-1.0.0->e-new-py'
```

The Python comparator exits with status 2 if the label does not match the
recordings (`labels.py`). The `--golden` directory must match the named
committed golden byte for byte. If the candidate side names a committed golden,
`--new` must also match it byte for byte. Otherwise the candidate must be
named in `catalog.json` under `comparisons`, which lists its allowed baselines.

The rules:

- **Only a `proven` entry covers a difference.** It carries evidence, a test id
  and a reviewer record (who reviewed it, the reviewed revision or a named
  retained review record, and the verdict). The four entries for Python
  transport changes use `record: python-transport-fixes-2026-10-28`, with an ISO review
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
- **Baselines.** The Python port is compared with `py-agentcc-1.0.0`. The
  catalog also records baselines for TypeScript comparisons by module format:
  `ts-client-1.0.1-*` for the client and `ts-integrations-1.0.0-*` for
  integrations. Rules for the step from TypeScript client 1.0.0 to 1.0.1
  apply only between those goldens.

`python/tests/gateway/parity/test_parity_enew.py` runs the comparison when
`fi.gateway` is importable and the environment matches the golden: Python 3.12
and the library versions in `index.json`, installed with
`-c e-old/constraints-py.txt`. The test reports a skip if the environment
differs and names each mismatch. For example, a CI run with a different
Pydantic version reports a skip rather than a parity pass.

**Twins.** Both languages' goldens use the same case IDs and input values for the
key and base-URL matrix, even where the languages resolve a conflict differently:
7 key sources by 8 base-URL sources, 9 URL shapes, `FI_*` /
`OPENAI_*` isolation, the `FI_API_KEY` and `FI_SECRET_KEY` guard cases, and the
import-time `AGENTCC_GATEWAY_URL` constant, read in a fresh process per case.
`test_parity_twins.py` compares the case IDs in the Python and TypeScript client
goldens, except for the language-specific cases listed under `twins` in
`catalog.json`. The Python catalog test also checks that the Python recorder's
case IDs match its committed golden.

`golden/MANIFEST.json` records the byte comparison of the two recording runs.
An independent reproduction needs the historical tools and inputs described
above, plus a comparison of the output against the committed goldens.

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
6. **TypeScript, `@agentcc/vercel` 1.0.0.** With no base URL it defaults to
   `https://api.agentcc.ai/v1` (`integration.vercel.defaults`,
   `integration.vercel.key_env_only`).
7. **TypeScript, 1.0.0 version.** The published 1.0.0 reports version `0.1.0` in
   `VERSION`, `User-Agent` and `x-agentcc-sdk-version`; the 1.0.1 recording
   reports `1.0.1` in all three fields (D-01c).
8. **TypeScript, a late stream error.** In 1.0.0 and 1.0.1 a consumer that
   stops at the `done` event does not receive an error frame sent after the finish and
   usage chunks; Python raises before `done`
   (`stream.extra.late_error_after_finish_reason.break_on_done`, D-16).
9. **Python, a closed client.** `close()` / `aclose()` drop the httpx client,
   and the next request builds a new one, so a closed client sends that request
   and succeeds (`resource.close`). The SDK leaves an injected `http_client`
   open (`resource.http_client`).
10. **Both, an empty argument falls through.** 1.x resolves the key and the base
    URL with `||` (TypeScript) and `or` (Python), so `apiKey: ""` /
    `api_key=""` sends the `AGENTCC_API_KEY` value, and an empty base URL uses
    `AGENTCC_BASE_URL` (`env.key_empty_arg_env.*`, `env.*.url_empty_arg_env`).
    A port that writes `??` or `is None` changes this, so the port decides.
11. **Both 1.x clients ignore `FI_GATEWAY_*`.** With `AGENTCC_*` and `FI_GATEWAY_*`
    both set, 1.x sends the `AGENTCC_*` value with no warning; with only
    `FI_GATEWAY_*` set it behaves as if nothing were set (no key in TypeScript,
    an `AgentCCError` in Python). In `fi.gateway`, `FI_GATEWAY_API_KEY` takes
    precedence over `AGENTCC_API_KEY`. After the explicit base-URL argument,
    Python reads `FI_GATEWAY_URL`, then `AGENTCC_BASE_URL`, then
    `FI_GATEWAY_BASE_URL`. The historical TypeScript port used the same key
    order but read `FI_GATEWAY_BASE_URL` before `AGENTCC_BASE_URL`. When an
    environment lookup finds conflicting values, `fi.gateway` emits one
    warning naming the variables and the selected source without their values.
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
