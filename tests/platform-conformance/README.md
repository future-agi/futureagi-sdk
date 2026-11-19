# Platform conformance kit

Language-neutral cases and runners that prove the Future AGI platform API (deployments, sandboxes,
agent runs, agents, schedules, environments and workspace reads) and the SDKs built on it behave the
same way. The contract is the scoped platform contract this repository publishes:
`openapi/platform/generated/futureagi-platform.openapi.json`.

## Layout

| Path | What it is |
|---|---|
| `cases/<family>/*.json` | The cases. Each names the call (method and path), the expected outcome, a tenant role, tags (`deterministic`, `mutating`, `failure`, `must-exist`, ...) and the `x-omega-sdk {family, method}` name the SDKs use. Schema: `schema/case-file.schema.json`. |
| `validate.mjs` | Validates every case against the schema and the contract (the SDK name must be the contract's), and checks that every operation of the contract has a case. |
| `runners/http/` | The `http` runner: raw HTTP, no SDK. It proves the contract itself. |
| `runners/sdk/`, `runners/{ts,py,fake}/` | The runner shells that load an SDK under test by path (see Bindings). `runners/py/worker.py` is the Python side. |
| `lib/` | Case loading and selection, the contract, expectations, error names, templates and the parity comparison. |
| `guards/no-prod-egress/` | The egress guard for Node (`index.mjs`) and Python (`no_prod_egress.py`). |
| `compare.json` | What "the fake matches the live service" means: exact fields, shape-only fields; an unlisted field fails. |

The cases state the contract only. A known server gap or a known contract drift is never written into
a case: a run passes `--expectations <file>` (`{ "cases": { "<id>": { "expectedFailure": { "owner",
"reason" }, "expect": { "knownDrift": ... } } } }`), and the receipt reports such a case as `xfail`
(or `xpass` once the gap closes) with its owner. `--cases <dir,...>` adds case directories kept
elsewhere (validated the same way) to a run.

```sh
node tests/platform-conformance/validate.mjs [--openapi <contract.json> --scope <scope.json>] [--sdk-root <generated-sdk-tree>] [--expectations <file>] [--out <receipt.json>]
```

The validator uses the same explicit operation scope as the contract and rejects mismatched inputs.
A wholly unavailable namespace retains every scenario as a **NOT-OFFERED** check: its route must be
absent from the contract and its operations absent from both generated SDK policy tables. Receipts
report every absence case and the total; these are not skipped tests. Missing operations within an
offered namespace remain failures. Route absence never validates security. Each of the six mandatory
security mechanisms has an offered capabilities-route counterpart with identical payloads and
expectations; missing, invalid or absence-only counterparts are hard errors. The original vehicle
bindings remain pinned even while hidden. `securityMustExist` lists only successfully validated,
offered cases, not merely present ids. Enabling sandboxes restores all 61 original sandbox-route
contract cases, including the six original security scenarios. Contract validation is not a
claim that a backend journey has run. For client-harness cases, the SDK runner passes only the
client specification to its binding; counterpart credit is contract-model proof, not a runtime
vehicle proof. The HTTP and SDK runtime runners remain separate proofs.

## Modes and tenants

| Mode | Credential |
|---|---|
| `fi-keypair` | the Future AGI key pair (`X-Api-Key`, `X-Secret-Key`) on the platform origin |
| `ee-key` | self-hosted EE: an EE account key as a Bearer token, with the `x-omega-org` / `x-omega-workspace` selectors |
| `fa-session` | a signed-in Future AGI app session on the platform origin (not an SDK credential) |
| `none` | no credential: the refusals that need none |

A case's `tenant` is `{org, role, resourceOrg, scopeOrg}`: `{org: "B", resourceOrg: "A"}` is org B's
credential on org A's resource (the cross-tenant cases expect 404, many 20 times in a row); adding
`scopeOrg: "A"` sends org B's credential with org A's scope selectors, which must be refused. Role
floors have one admitting and one refusing case each (admin: `platform.agents.retire.*`; member:
`sandboxes.create.member`; viewer: `sandboxes.list.viewer`).

## Running the http runner

```sh
node tests/platform-conformance/runners/http/run.mjs --target gateway --base <platform origin> \
  --mode fi-keypair --fixtures <secrets.json> --world <ids.json> --exporter <otlp url> --out <dir> \
  [--expectations <file>] [--only 'sandboxes.*'] [--allow <host,...>]
```

`--fixtures` holds the credentials per org and role (never written to a receipt); `--world` the ids
of the resources the cases need (a sandbox, an agent, a run, a deployment per org). `plain` is the
built-in harness. Cases that need a fault proxy, a feature toggle or a scripted fixture run through a
harness module: `--harness <name> --harnesses <module.mjs>`, where the module exports
`harnesses = { <name>: async ({ base, makeExecutor, fetchImpl, flags, fixtures }) => ({ run, close }) }`.

## The egress guard

Every runner calls `requireEndpoints()` first: it refuses to start when a base URL or the span
exporter endpoint is unset or names a refused host. The rule (`classify.mjs`, mirrored in
`no_prod_egress.py`): any host in the production zone (`futureagi.com`, `*.futureagi.com`) is refused
even if listed; loopback is allowed; anything else only from the run's allowlist. It is decided on the
host name, before any DNS query. The first refusal trips the guard; the trip is recorded whether or
not the SDK swallows the error, and the run exits 3. The fake runner denies the network outright.

The guard is armed per process before the SDK under test is imported. In Node it covers the fetch
handed to the binding and `globalThis.fetch`, `http(s).request/get`, every `net.Socket#connect`,
`dns.lookup` and `resolve*`, refuses `worker_threads.Worker`, and wraps the span exporter. In the
Python worker it covers the httpx transports handed to the binding, `socket.getaddrinfo` and
`gethostbyname`, `socket.socket.connect`, `connect_ex` and `sendto` (so an SDK's own clients are
caught), and refuses importing `grpc` or `pycurl`. A child process and native code other than those
modules are outside an in-process guard.

## Bindings (how an SDK runs this suite)

```sh
node tests/platform-conformance/runners/ts/run.mjs   --client-ts <package dir> --base <url> --mode fi-keypair --fixtures <f> --world <w> --exporter <url> --out <dir>
node tests/platform-conformance/runners/py/run.mjs   --client-py <dir with conformance_binding.py> [--python <bin>] ...
node tests/platform-conformance/runners/fake/run.mjs --testkit <test kit dir> ...
```

A binding maps a case's `x-omega-sdk {family, method}` name and neutral `args` onto the SDK's public
API (`openapi/platform/wrapper-map.json` gives each method's path in both languages): `createClient`,
`call(client, {family, method}, args)`, `describeError(error)` (onto the neutral error names in
`lib/errors.mjs`) and, for the client-side must-exist cases, `clientCase(spec)`. TypeScript and the
fake load `<dir>/conformance/binding.mjs`; Python loads the module `conformance_binding` from
`--client-py`. The stubs in `runners/test/` are the reference. The shells pass the guarded transport
to `createClient`; an SDK that ignores it is still guarded by the process-wide layer.

## Tests

```sh
node --test tests/platform-conformance/test/*.test.mjs tests/platform-conformance/guards/no-prod-egress/test/*.test.mjs
SDKCONF_PYTHON=<python with httpx> node --test tests/platform-conformance/runners/test/shells.test.mjs
<python with httpx> -I -B -m unittest discover -s tests/platform-conformance/guards/no-prod-egress/test -p 'test_*.py'
```
