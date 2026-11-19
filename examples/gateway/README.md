# Gateway framework examples

These examples exercise the **source-only gateway preview**, not the currently
published SDK. The release wheel and tarball still omit the gateway. A green mock
test does not enable it or qualify a hosted backend.

The examples use the frameworks' real clients. `MockAgentCC` supplies responses
through a loopback HTTP bridge in tests; LangChain, LlamaIndex, the Vercel AI SDK,
the Express middleware, React hook and Next.js route are not replaced by mocks.
No provider or hosted API is contacted by the tests.

## Examples

| Framework | Python | TypeScript |
| --- | --- | --- |
| LangChain | `python/langchain_chat.py`: `ChatOpenAI` with `openai_kwargs`, async and sync | `typescript/langchain.ts`: `ChatOpenAI` with `openaiOptions` |
| LlamaIndex | `python/llamaindex_chat.py`: `OpenAILike`, async and sync | Not offered in this example set: `OpenAILike` is a Python class |
| Vercel AI SDK | Not offered: JavaScript framework | `typescript/vercel.ts`: `createOpenAI(aiSdkProviderSettings(...))` |
| Express | Not offered: JavaScript framework | `typescript/express.ts`: session middleware and a loopback HTTP server |
| React + Next.js | Not offered: JavaScript frameworks | `typescript/app/chat.tsx` and `typescript/app/api/chat/route.ts`: hook in route mode, streaming answer |

The Python helpers return `base_url`, whereas LlamaIndex calls it `api_base`.
Both helpers already append exactly one `/v1`. Do not append another.

## Prepare and test the source preview

Run these commands on a disposable Linux cloud worker with Node 22, npm and uv.
From the repository root:

```sh
bash examples/gateway/ci/prepare.sh
bash examples/gateway/ci/test.sh
```

`PYTHON_VERSION=3.10` selects the Python floor; the default is 3.12. Preparation
installs the committed example lockfiles and builds the gateway TypeScript
subpaths. It copies the built gateway bytes and the unchanged SDK package manifest
into the example's dependencies, so its actual export map and the consumer's React
peer are used. No package is published or installed from a pretend SDK release.

The test phase permits only loopback sockets. Tests assert the path, model,
session header and explicit gateway credential, and check missing keys,
platform-key refusal, bad input, upstream failure and React rendering. A
non-loopback connection canary proves each test guard is active. Test dependencies
are optional, isolated in this directory, and do not become SDK dependencies.

Regenerate the example dependency locks with `bash examples/gateway/ci/lock.sh`
on a cloud worker, then commit the generated files. Never edit lockfiles by hand.

## Run against your own local gateway

Create your **personal gateway key explicitly** in an interactive Console
session. It is not your `FI_API_KEY` / `FI_SECRET_KEY` platform pair. Do not fetch an
organization key, generate a key automatically or place a provider key here.
Set these server-side values without committing them or printing the key:

```sh
export FI_GATEWAY_API_KEY='<your personal gateway key>'
export FI_GATEWAY_BASE_URL='http://127.0.0.1:8090'
export FI_GATEWAY_MODEL='<a model served by your local gateway>'
```

After preparation, from the repository root:

```sh
PYTHONPATH="$PWD/python" .gateway-examples-venv/bin/python examples/gateway/python/langchain_chat.py
PYTHONPATH="$PWD/python" .gateway-examples-venv/bin/python examples/gateway/python/llamaindex_chat.py
```

For the TypeScript examples:

```sh
cd examples/gateway/typescript
npm run langchain
npm run vercel
npm run express
# In a separate terminal, with the same server-side configuration:
npm run dev
```

The Next.js app listens on `http://127.0.0.1:3000`. The Express app listens on
`http://127.0.0.1:3001`; POST `{"messages":[{"role":"user","content":"Hello"}]}`
to `/api/chat` with `Content-Type: application/json`. Express uses `x-request-id`
as the session identifier, or generates one when absent.

These are **local development demos**, not authenticated public proxies. Before
deploying either server, add application session authorization, request-size
limits at the HTTP edge, per-person rate limits and budget controls. Never put a
gateway key in `NEXT_PUBLIC_*`, a React provider, browser storage or browser
request headers. The route selects its own model and ignores browser overrides.
The React Stop control stops reading; it does not promise upstream cancellation.

Stock OpenAI framework streaming can miss a gateway cache-hit JSON response.
The stock-framework examples therefore use non-streaming calls. The Next.js
example uses the SDK's native streaming helper. These examples make no claims
about request-level retry, fallback or mirror settings that the gateway ignores.
Python's stock OpenAI client may read `OPENAI_ORG_ID` and `OPENAI_PROJECT_ID`;
unset those before using a gateway if they should not be forwarded.

Mock success covers the client wiring only. Hosted streaming, revoked-key
behaviour and release availability still require backend and artifact
qualification; these examples do not replace that check.
