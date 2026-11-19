import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../errors";
import { GatewayConfigWarningError } from "../fa-management";
import { scrubText } from "../redact";

function make(handler: (request: Request) => Response | Promise<Response>, options = {}) {
  return new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9012", retries: 0,
    fetch: (async (input: any, init?: RequestInit) => handler(new Request(input, init))) as typeof fetch, ...options });
}

const pairs = [
  ["abcd", "abcd-opaque-provider-value"],
  ["abcd", "opaque-provider-value-abcd"],
  ["abcd", "opaque-abcd-provider-value"],
  ['x.*[y]\\"', 'x.*[y]\\"-opaque-provider-value'],
  ["redacted", "redacted-opaque-provider-value"],
] as const;
const orders = pairs.flatMap(([short, long]) => [false, true].map(reverse => ({ short, long, reverse })));

it.each(orders.flatMap(pair => ["create", "update", "rotate"].map(method => ({ ...pair, method }))))(
  "redacts whole overlapping values in $method: $short / $long reversed=$reverse", async ({ short, long, reverse, method }) => {
    const entries = [["api_key", short], ["secret_key", long]];
    const body = { credentials: Object.fromEntries(reverse ? entries.reverse() : entries) };
    const response = { diagnostic: `${long} | ${short}`, details: [{ echo: long }], credentials: { api_key: long } };
    const client = make(async request => {
      expect(await request.json()).toEqual(body);
      return Response.json({ status: true, result: response });
    });
    const credentials = client.gateway.providerCredentials;
    const call = method === "create" ? credentials.create(body) : method === "update" ? credentials.update("provider", body) : credentials.rotate("provider", body);
    const result = await call.withResponse();
    expect(result.data).toEqual({ diagnostic: "[redacted] | [redacted]", details: [{ echo: "[redacted]" }], credentials: { api_key: "[REDACTED]" } });
    expect(response.diagnostic).toBe(`${long} | ${short}`);
  });

it.each(orders)("scrubs text in one literal pass: $short / $long reversed=$reverse", ({ short, long, reverse }) => {
  expect(scrubText(`${long} | ${short}`, reverse ? [long, short] : [short, long])).toBe("[redacted] | [redacted]");
});

const warningCases = ["a", "gateway_synced", "gateway_warning", "warnings", "status", "result", "credentials", "hasWarnings"].flatMap(secret =>
  ["gateway_synced", "gateway_warning", "warnings", "none"].flatMap(trigger =>
    ["body", "auth"].map(source => ({ secret, trigger, source }))));

it.each(warningCases)("preserves warning semantics and keys: $secret / $trigger / $source", async ({ secret, trigger, source }) => {
  const response = { gateway_synced: trigger !== "gateway_synced", warnings: trigger === "warnings" ? [secret] : [],
    gateway_warning: trigger === "gateway_warning" ? secret : "", diagnostic: secret,
    details: [{ warnings: secret, a: secret }], credentials: { api_key: secret } };
  const body = source === "body" ? { credentials: { api_key: secret } } : {};
  const client = make(() => Response.json({ status: true, result: response }), source === "auth" ? { apiKey: secret } : {});
  const invoke = (strict: boolean) => client.gateway.providerCredentials.rotate("provider", body, {}, { strict }).withResponse();
  const result = await invoke(false);
  const expected = { ...response, diagnostic: "[redacted]", details: [{ warnings: "[redacted]", a: "[redacted]" }],
    credentials: { api_key: "[REDACTED]" }, warnings: trigger === "warnings" ? ["[redacted]"] : [],
    gateway_warning: trigger === "gateway_warning" ? "[redacted]" : "", ...(trigger === "none" ? {} : { hasWarnings: true }) };
  expect(result.data).toEqual(expected);
  if (trigger === "none") {
    expect((await invoke(true)).data).toEqual(expected);
  } else {
    await expect(invoke(true)).rejects.toBeInstanceOf(GatewayConfigWarningError);
    await expect(invoke(true)).rejects.toMatchObject({ code: "gateway_config_warning" });
  }
  expect(response.diagnostic).toBe(secret);
});

it.each(["a", "status", "result", "error_code"])("keeps false-status envelopes as errors for auth credential %s", async secret => {
  const client = make(() => Response.json({ status: false, result: { error_code: "rejected", message: secret } }), { apiKey: secret });
  await expect(client.gateway.config.getActive()).rejects.toBeInstanceOf(BadRequestError);
});

const httpPairs = [
  ["a", "fixture-secret"], ["ab", "fixture-secret"], ["abc", "fixture-secret"],
  ["details", "fixture-secret"], ["message", "fixture-secret"],
  ["error_code", "fixture-secret"], ["redacted", "fixture-secret"],
  ["abcd", 'abcd"opaque-provider-value'], ["abcd", 'opaque-provider-value"abcd'],
  ["abcd", 'opaque"abcd"provider-value'], ["abcd", "abcd\\opaque-provider-value"],
  ["abcd", "abcd/opaque-provider-value"],
] as const;
const httpCases = httpPairs.flatMap(([short, long]) => [false, true].flatMap(reverse =>
  ["auth", "mixed"].map(source => ({ short, long, reverse, source }))));

it.each(httpCases)("scrubs decoded HTTP error values once: $short / $long reversed=$reverse source=$source", async ({ short, long, reverse, source }) => {
  const [first, second] = reverse ? [long, short] : [short, long];
  const body = source === "mixed" ? { credentials: { api_key: second } } : undefined;
  const response = { status: false, result: { error_code: "rejected", message: `${first} | ${second}`,
    diagnostic: `${second} | ${first}`, details: [{ details: first, message: second }], credentials: { api_key: second } } };
  const client = make(async request => {
    if (body !== undefined) expect(await request.json()).toEqual(body);
    // Construct the JSON Unicode escape visibly; the response still exercises
    // decoded redaction rather than hiding printable source text in a literal.
    const escapedSlash = "\\" + "u" + "/".charCodeAt(0).toString(16).padStart(4, "0");
    return new Response(JSON.stringify(response).replace(/\//gu, escapedSlash), { status: 400, headers: {
      "x-request-id": "request-fixture", "x-upstream-request-id": "upstream-fixture",
      "x-omega-receipt-id": "receipt-fixture", "retry-after": "7",
    } });
  }, { apiKey: first, secretKey: source === "auth" ? second : "fixture-secret" });
  const call = body === undefined ? client.gateway.config.getActive() : client.gateway.providerCredentials.rotate("provider", body);
  const error = await call.withResponse().then(() => { throw new Error("Expected HTTP error"); }, (e: unknown) => e);
  expect(error).toBeInstanceOf(BadRequestError);
  const name = body === undefined ? "gateway.config.get_active" : "gateway.provider_credentials.rotate";
  expect(error).toMatchObject({
    statusCode: 400, code: "rejected", operation: name, requestId: "request-fixture",
    upstreamRequestId: "upstream-fixture", receiptId: "receipt-fixture", retryAfter: 7,
    message: `${name} failed with status 400 (rejected): [redacted] | [redacted] (request id request-fixture)`,
  });
  expect((error as BadRequestError).payload).toEqual({ status: false, result: { error_code: "rejected",
    message: "[redacted] | [redacted]", diagnostic: "[redacted] | [redacted]",
    details: [{ details: "[redacted]", message: "[redacted]" }], credentials: "[redacted]" } });
  expect(response.result.message).toBe(`${first} | ${second}`);
});
