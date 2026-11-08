# Future AGI TypeScript SDK Compliance Adapter

Thin HTTP adapter used by `futureagi-sdk-test-harness`.

It wraps the TypeScript `@future-agi/sdk` package and exposes the shared adapter contract:

- `GET /health`
- `POST /init`
- `POST /reset`
- `GET /state`
- `POST /raw-request`
- `POST /annotation/log`
- `POST /annotation/metadata`
- `POST /annotation-queue/lifecycle`
- `POST /annotation-queue/management`
- `POST /annotation-score/lifecycle`
- `POST /dataset/lifecycle`
- `POST /dataset/management`
- `POST /knowledge-base/lifecycle`
- `POST /prompt/lifecycle`
- `POST /provider-api-key/lifecycle`

Model logging is not currently claimed by this adapter because the current
backend does not expose `/sdk/api/v1/log/model/` or `/log/model/`.

## Local Run

From `typescript/futureagi`:

```bash
npm ci
PORT=8080 npx tsx tests/compliance/adapter.ts
```

Then run the harness from `../futureagi-sdk-test-harness`:

```bash
uv run futureagi-sdk-test-harness run --adapter-url http://127.0.0.1:8080
```

## Docker

From the `futureagi-sdk` repo root:

```bash
docker build -f typescript/futureagi/tests/compliance/Dockerfile -t futureagi-sdk-typescript-adapter .
docker run --rm -p 8080:8080 futureagi-sdk-typescript-adapter
```
