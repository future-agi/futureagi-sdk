import { readFileSync } from "node:fs";
import path from "node:path";
import * as SDK from "../../index";
import { FutureAGIClient } from "../../futureagi-client";
import { FutureAGIAPIError, NotFoundError } from "../errors";
import { PlatformCore } from "../platform-base";
import { resolvePlatformOrigin } from "../origins";

// Frozen source-backed FA/EE bodies shared with Python; never call a service.
const fixture: {
  fa_unrouted: { body: string; content_type: string };
  ee: Array<{ id: string; body: unknown; class: string; code: string }>;
} = JSON.parse(readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/server-contracts/console-404.json"), "utf8"));
const sources = ["derived", "env", "argument"] as const;
type Source = typeof sources[number];
const namespaces = ["agents.get", "agents.runs.get", "agents.schedules.get", "environments.get", "connectors.get", "credentials.get"];
const explicitUrl = "https://console.futureagi.com:8443/private-origin-path";
const hosted = "Hosted Future AGI does not support Console access through the SDK in this release";
const env = { ...process.env };

beforeEach(() => {
  for (const key of Object.keys(process.env)) if (key.startsWith("FI_")) delete process.env[key];
});
afterEach(() => { process.env = { ...env }; });

function make(source: Source, response: () => Response, apiKey = "fixture-api-key") {
  if (source === "env") process.env.FI_PLATFORM_BASE_URL = explicitUrl;
  const fetch_ = jest.fn(async () => response());
  const client = new FutureAGIClient({ apiKey, secretKey: "fixture-secret-key", baseUrl: "https://api.futureagi.com",
    ...(source === "argument" ? { platformBaseUrl: explicitUrl } : {}), retries: 0, fetch: fetch_ });
  return { client, fetch_ };
}

async function invoke(client: FutureAGIClient, name: string): Promise<unknown> {
  const parts = name.split(".");
  let target: any = client;
  for (const part of parts.slice(0, -1)) target = target[part];
  return target[parts[parts.length - 1]!]!("missing-id");
}

function faResponse(status = 404): Response {
  return new Response(fixture.fa_unrouted.body, { status, headers: {
    "content-type": fixture.fa_unrouted.content_type, "x-request-id": "fa-request",
  } });
}

async function failure(call: PromiseLike<unknown>): Promise<FutureAGIAPIError> {
  return call.then(() => { throw new Error("expected HTTP failure"); }, (error: unknown) => {
    expect(error).toBeInstanceOf(FutureAGIAPIError);
    return error as FutureAGIAPIError;
  });
}

describe.each(sources)("%s origin", (source) => {
  test.each(namespaces)("%s: FA unrouted 404 is ConsoleUnavailableError", async (namespace) => {
    const { client, fetch_ } = make(source, faResponse);
    const error = await failure(invoke(client, namespace));
    expect(error).toBeInstanceOf(NotFoundError);
    expect(error.constructor.name).toBe("ConsoleUnavailableError");
    expect(error.getErrorCode()).toBe("CONSOLE_UNAVAILABLE");
    expect(error.statusCode).toBe(404);
    expect(error.code).toBe("http_404");
    expect(error.requestId).toBe("fa-request");
    const host = source === "derived" ? "api.futureagi.com" : "console.futureagi.com:8443";
    expect(error.message.startsWith(`The Console API is not available at ${host}.`)).toBe(true);
    expect(error.message).toContain(hosted);
    if (source === "derived") {
      expect(error.message).toContain("for self-hosted Enterprise, set FI_PLATFORM_BASE_URL to your Console API origin");
    } else {
      expect(error.message.toLowerCase()).toContain("check");
      expect(error.message).toContain("FI_PLATFORM_BASE_URL");
      expect(error.message).not.toContain("set FI_PLATFORM_BASE_URL");
    }
    for (const forbidden of ["fixture-api-key", "fixture-secret-key", "private-origin-path", "missing-id", "<html", "https://"]) {
      expect(error.message).not.toContain(forbidden);
    }
    expect(fetch_).toHaveBeenCalledTimes(1);
  });

  test.each(fixture.ee)("EE $id keeps its existing class", async (row) => {
    const { client, fetch_ } = make(source, () => new Response(JSON.stringify(row.body), { status: 404 }));
    const error = await failure(invoke(client, "agents.get"));
    expect(error).toBeInstanceOf(NotFoundError);
    expect(error.constructor.name).toBe(row.class);
    expect(error.code).toBe(row.code);
    expect(error.message).not.toContain("Console API is not available");
    expect(fetch_).toHaveBeenCalledTimes(1);
  });
});

test("envelope detection precedes secret scrubbing", async () => {
  const { client, fetch_ } = make("derived", () => new Response(JSON.stringify(fixture.ee[0]!.body), { status: 404 }), "not_found");
  const error = await failure(invoke(client, "agents.get"));
  expect(error.constructor).toBe(NotFoundError);
  expect(error.message).not.toContain("not_found");
  expect(fetch_).toHaveBeenCalledTimes(1);
});

test.each([[403, "PermissionDeniedError"], [500, "CoreServerError"]])("non-404 %s is unchanged", async (status, expected) => {
  const { client, fetch_ } = make("derived", () => faResponse(Number(status)));
  const error = await failure(invoke(client, "agents.get"));
  expect(error.constructor.name).toBe(expected);
  expect(fetch_).toHaveBeenCalledTimes(1);
});

test("FA management 404 is not ConsoleUnavailableError", async () => {
  const fetch_ = jest.fn(async () => faResponse());
  const core = new PlatformCore({ resolveOrigin: () => resolvePlatformOrigin({ apiKey: "fixture-api-key", secretKey: "fixture-secret-key", baseUrl: "https://api.futureagi.com" }, {}),
    table: { "gateway.keys.get": { name: "gateway.keys.get", family: "gateway", method: "GET", path: "/agentcc/keys/missing/" } }, fetch: fetch_ });
  const error = await failure(core.call("gateway.keys.get"));
  expect(error.constructor).toBe(NotFoundError);
  expect(fetch_).toHaveBeenCalledTimes(1);
});

describe.each(sources)("%s incomplete response", (source) => {
  describe.each([fixture.ee[0]!, fixture.ee[5]!])("EE $id", (row) => {
    test.each(["capped", "interrupted", "empty-interrupted"])("%s 404 is status-only", async (readKind) => {
      // OmegaEeError.detail is unbounded: extend the frozen body to exercise the SDK cap.
      const body = { ...(row.body as Record<string, unknown>), detail: { context: "x".repeat(70 * 1024) } };
      let raw = new TextEncoder().encode(JSON.stringify(body));
      if (readKind !== "capped") raw = raw.slice(0, readKind === "interrupted" ? 80 : 0);
      let offset = 0;
      let closed = false;
      const stream = new ReadableStream<Uint8Array>({
        pull(controller) {
          if (offset < raw.length) {
            controller.enqueue(raw.slice(offset, offset + 8192));
            offset += 8192;
          } else if (readKind !== "capped") {
            closed = true;
            controller.error(new Error("fixture stream interrupted"));
          } else {
            closed = true;
            controller.close();
          }
        },
        cancel() { closed = true; },
      }, { highWaterMark: 0 });
      const { client, fetch_ } = make(source, () => new Response(stream, { status: 404, headers: { "x-request-id": "ee-request" } }));
      const error = await failure(invoke(client, "agents.get"));
      expect(error.constructor).toBe(NotFoundError);
      expect(error.code).toBe("http_404");
      expect(error.requestId).toBe("ee-request");
      expect(error.message).not.toContain("Console API is not available");
      expect(fetch_).toHaveBeenCalledTimes(1);
      expect(closed).toBe(true);
      expect(offset).toBeLessThanOrEqual(64 * 1024);
    });
  });
});

// Compatibility check: readCapped keeps a whole first chunk, so this is still parseable.
// The chunked/interrupted cases above are the RED regression for incomplete EE evidence.
test("oversized single-chunk EE 404 is not ConsoleUnavailableError", async () => {
  const body = { ...(fixture.ee[0]!.body as Record<string, unknown>), detail: { context: "x".repeat(70 * 1024) } };
  const { client, fetch_ } = make("derived", () => new Response(JSON.stringify(body), { status: 404 }));
  const error = await failure(invoke(client, "agents.get"));
  expect(error.constructor).toBe(NotFoundError);
  expect(fetch_).toHaveBeenCalledTimes(1);
});

test.each(sources)("%s oversized HTML 404 is conservatively status-only", async (source) => {
  // A capped HTML response is not complete evidence, even with a text/html header.
  const raw = new TextEncoder().encode(fixture.fa_unrouted.body.repeat(512));
  let offset = 0;
  let closed = false;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (offset < raw.length) {
        controller.enqueue(raw.slice(offset, offset + 8192));
        offset += 8192;
      } else {
        controller.close();
      }
    },
    cancel() { closed = true; },
  }, { highWaterMark: 0 });
  const { client, fetch_ } = make(source, () => new Response(stream, { status: 404, headers: { "content-type": "text/html" } }));
  const error = await failure(invoke(client, "agents.get"));
  expect(error.constructor).toBe(NotFoundError);
  expect(error.code).toBe("http_404");
  expect(fetch_).toHaveBeenCalledTimes(1);
  expect(closed).toBe(true);
  expect(offset).toBeLessThanOrEqual(64 * 1024);
});

test("ConsoleUnavailableError is exported from the public index", () => {
  expect(SDK).toHaveProperty("ConsoleUnavailableError");
  const ctor = (SDK as unknown as Record<string, typeof NotFoundError>).ConsoleUnavailableError!;
  expect(new ctor(404, undefined)).toBeInstanceOf(NotFoundError);
});
