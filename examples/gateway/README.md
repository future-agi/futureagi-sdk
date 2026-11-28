# Gateway framework examples for Python

These examples use the Python gateway client from a source checkout. The
`futureagi` wheel and sdist include `fi.gateway`. The tests exercise the real
framework clients against `MockAgentCC` through a loopback HTTP bridge; they
check client wiring, not a live backend.

| Framework | Example |
| --- | --- |
| LangChain | [`python/langchain_chat.py`](python/langchain_chat.py): `ChatOpenAI` with `openai_kwargs`, async and sync |
| LlamaIndex | [`python/llamaindex_chat.py`](python/llamaindex_chat.py): `OpenAILike`, async and sync |

`openai_kwargs` returns `base_url` with the `/v1` suffix. The LlamaIndex
example passes that value as `api_base` without adding another suffix.

## Prepare and test

From the repository root on a Linux worker with uv:

```sh
bash examples/gateway/ci/prepare.sh
bash examples/gateway/ci/test.sh
```

Preparation installs the locked example dependencies in an isolated virtual
environment. `PYTHON_VERSION=3.10` selects the Python floor; the default is 3.12.
The example dependencies are separate from the SDK's dependencies.

The tests check the request path, model, session header, and gateway credential
for sync and async calls. They also verify that a missing gateway key does not
fall back to a provider key and that the platform key pair is rejected. A socket
canary checks that non-loopback connections are blocked.

To regenerate the dependency lock, run `bash examples/gateway/ci/lock.sh`.
Use the generated [`requirements.lock`](python/requirements.lock) without
manual edits.

## Run against your own local gateway

Create a personal gateway key in an interactive Console session. Use that key,
not an organization key, provider key, or the `FI_API_KEY` / `FI_SECRET_KEY`
platform pair. Set the following server-side values without committing or
printing the key:

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

Both examples use non-streaming calls. The frameworks' OpenAI client may read
`OPENAI_ORG_ID` and `OPENAI_PROJECT_ID`; unset those variables if the gateway
should not receive them.
