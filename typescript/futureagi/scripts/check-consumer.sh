#!/usr/bin/env bash
# The package as a user installs it: pack the built package, install the tarball into an empty
# project, compile consumer/*.mts against it (type-level: every public call there must
# type-check from the published .d.ts files, not from this repository's sources), then load it
# as ESM and as CommonJS. Run after `pnpm run build`; CI runs it on every pull request.
set -euo pipefail

pkg=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

[ -d "$pkg/dist/esm" ] || { echo "build first: pnpm run build" >&2; exit 1; }
tarball=$(cd "$pkg" && npm pack --ignore-scripts --pack-destination "$work" 2>/dev/null | tail -1)
cd "$work"
npm init -y >/dev/null
npm install --no-audit --no-fund --silent "./$tarball" "typescript@5.6.3"
cp "$pkg"/consumer/*.mts "$pkg"/consumer/tsconfig.json .
# Every TypeScript example of the generated reference, and its documented imports, as one
# more consumer module: an example that does not compile against the packed package fails here.
node "$pkg/scripts/docs-examples.mjs" "$pkg/../../docs/sdk-reference" docs-examples.mts

echo "consumer: tsc against $tarball (consumer-types.mts + docs-examples.mts)"
npx tsc -p tsconfig.json

echo "consumer: ESM import"
node --input-type=module -e '
  import { Client, platform } from "@future-agi/sdk";
  import { Datasets } from "@future-agi/sdk/platform";
  const c = new Client({ apiKey: "x", secretKey: "y", baseUrl: "http://127.0.0.1:9", maxRetries: 0, timeout: 500 });
  if (!(c.datasets instanceof Datasets) || typeof c.knowledgeBases.create !== "function" || typeof c.fileKnowledgeBases.files.list !== "function") throw new Error("resources missing");
  if (typeof platform.Client !== "function") throw new Error("platform namespace missing");
'
echo "consumer: a real HTTP 429 is caught as the documented platform RateLimitError"
node --input-type=module -e '
  import http from "node:http";
  import { Client } from "@future-agi/sdk";
  import { RateLimitError, APIError } from "@future-agi/sdk/platform";
  const server = http.createServer((req, res) => { res.writeHead(429, { "content-type": "application/json", "retry-after": "0" }); res.end(JSON.stringify({ detail: "slow down" })); });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const c = new Client({ apiKey: "x", secretKey: "y", baseUrl: `http://127.0.0.1:${server.address().port}`, maxRetries: 0, timeout: 2000 });
  try {
    await c.account.whoami();
    throw new Error("expected a 429 to throw");
  } catch (error) {
    if (!(error instanceof RateLimitError) || !(error instanceof APIError) || error.status !== 429) throw new Error(`429 did not surface as the platform RateLimitError: ${error}`);
  } finally {
    server.close();
  }
'
echo "consumer: CommonJS require"
node -e '
  const { Client } = require("@future-agi/sdk");
  const { Datasets } = require("@future-agi/sdk/platform");
  const c = new Client({ apiKey: "x", secretKey: "y", baseUrl: "http://127.0.0.1:9", maxRetries: 0, timeout: 500 });
  if (!(c.datasets instanceof Datasets)) throw new Error("@future-agi/sdk/platform does not export the resource classes");
'
echo "consumer: ok"
