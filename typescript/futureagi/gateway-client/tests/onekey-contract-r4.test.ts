import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as parts from "../src/request-parts.js";
import { refusalRetry } from "../src/refusal-policy.js";
import { refusal } from "./onekey-test-helpers.js";

// Structural views let the behavioral RED compile before the additive API exists.
type Evidence = Readonly<{ dispatched: boolean | "unknown"; gatewayRequestId: string | null; clientRequestId: string | null }>;
type View = { gatewayEvidence?: Evidence; gatewayRequestId?: string | null; dispatched?: boolean | "unknown"; clientRequestId?: string | null; model?: string | null; candidates?: string[] | null };
type Parser = (headers?: Headers | readonly (readonly [string, string])[], options?: { headersObservable?: boolean; cardinalityObservable?: boolean }) => Evidence;
const api = gateway as unknown as { parseGatewayEvidence?: Parser; getGatewayEvidence?: (response: Response) => Evidence };
const view = (value: unknown) => value as View;
const ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV";
const ID2 = "01ARZ3NDEKTSV4RRFFQ69G5FAW";
const HEADERS = { "x-agentcc-request-id": ID, "x-agentcc-dispatched": "false", "x-agentcc-client-request-id": "client-correlation", "retry-after": "2" };
const REQUEST = { method: "POST", path: "/v1/chat/completions", body: { model: "example/model", messages: [] } };
const PATHS = ["request", "requestWithResponse", "requestRaw", "requestStream"] as const;
const ROWS = [
  { status: 403, code: "managed_model_unpriced", category: "permission", name: "PermissionDeniedError", remedy: "Choose a priced model or use your own provider key.", metadata: { model: "provider/team/model-variant", reason: "unpriced", future: null } },
  { status: 400, code: "managed_model_ambiguous", category: "generic", name: "BadRequestError", remedy: "Choose a provider-prefixed candidate ID or use the organization's own provider key for a candidate.", metadata: { model: "model", candidates: ["first/team/model-variant", "second/model"] } },
  { status: 400, code: "managed_resource_unsupported", category: "generic", name: "BadRequestError", remedy: "Use a supported managed request shape or your own provider key.", metadata: undefined },
];
let sleep: jest.SpiedFunction<typeof parts.sleep>;
beforeEach(() => { sleep = jest.spyOn(parts, "sleep").mockResolvedValue(undefined); });
afterEach(() => { jest.restoreAllMocks(); });
function client(fetch: typeof globalThis.fetch, extra: gateway.ClientOptions = {}) {
  return new gateway.AgentCC({ apiKey: "offline-test", baseUrl: "https://gateway.test", maxRetries: 5, ...extra, fetch });
}
function parse(headers?: Parameters<Parser>[0], options?: Parameters<Parser>[1]): Evidence {
  expect(typeof api.parseGatewayEvidence).toBe("function");
  return api.parseGatewayEvidence!(headers, options);
}

for (const path of PATHS) describe(`contract evidence ${path}`, () => {
  for (const row of ROWS) it(`${row.code} is typed and terminal`, async () => {
    const metadata = row.metadata && { ...row.metadata, dispatched: true, request_id: "untrusted", extra: { nullable: null } };
    const body = { type: "error", error: { code: row.code, type: "unrelated", message: "translated", param: "input", ...(metadata ? { metadata } : {}) } };
    const fetch = jest.fn<typeof globalThis.fetch>(async () => new Response(JSON.stringify(body), { status: row.status, headers: HEADERS }));
    const error = await refusal(client(fetch)[path](REQUEST));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
    expect(error).toMatchObject({ name: row.name, category: row.category, remedy: row.remedy, body, requestId: ID });
    expect(view(error).gatewayEvidence).toEqual({ dispatched: false, gatewayRequestId: ID, clientRequestId: "client-correlation" });
    expect(view(error).model).toBe(row.metadata?.model ?? null);
    expect(view(error).candidates).toEqual("candidates" in (row.metadata ?? {}) ? row.metadata!.candidates : null);
    expect(error.metadata).toEqual(metadata ?? null);
    expect(JSON.parse(JSON.stringify(view(error).gatewayEvidence))).toEqual(view(error).gatewayEvidence);
  });

  it.each(["False", "FALSE", "false, false", "false,true", " false ", "", "0"])("invalid dispatch %p cannot authorize no-code retry", async (dispatched) => {
    const fetch = jest.fn<typeof globalThis.fetch>(async () => new Response("{}", { status: 503, headers: { ...HEADERS, "x-agentcc-dispatched": dispatched } }));
    const error = await refusal(client(fetch)[path](REQUEST));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(view(error).dispatched).toBe("unknown");
  });

  it("captures immutable evidence before reading body or invoking callbacks", async () => {
    const response = new Response("{}", { status: 503, headers: HEADERS });
    const original = response.json.bind(response);
    jest.spyOn(response, "json").mockImplementation(async () => {
      response.headers.set("x-agentcc-request-id", ID2);
      response.headers.set("x-agentcc-dispatched", "true");
      return original();
    });
    const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
    const errors: unknown[] = [];
    const callback = new class extends gateway.CallbackHandler {
      override onError(_request: gateway.CallbackRequest, error: Error) { errors.push(error); }
    }();
    const error = await refusal(client(fetch, { maxRetries: 0, callbacks: [callback] })[path](REQUEST));
    expect(view(error).gatewayEvidence).toEqual({ dispatched: false, gatewayRequestId: ID, clientRequestId: "client-correlation" });
    expect(Object.isFrozen(view(error).gatewayEvidence)).toBe(true);
    expect(view(errors[0]).gatewayEvidence).toBe(view(error).gatewayEvidence);
    expect(error.requestId).toBe(ID);
  });

  it("isolates each retry's evidence", async () => {
    const fetch = jest.fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(new Response("{}", { status: 503, headers: HEADERS }))
      .mockResolvedValueOnce(new Response("{}", { status: 503, headers: { ...HEADERS, "x-agentcc-request-id": ID2, "x-agentcc-dispatched": "true" } }));
    const error = await refusal(client(fetch)[path](REQUEST));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(view(error).gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: ID2, clientRequestId: "client-correlation" });
  });

  it("CORS-hidden absent identity does not open the legacy replay exception", async () => {
    const response = new Response("{}", { status: 503 });
    Object.defineProperty(response, "type", { value: "cors" });
    const fetch = jest.fn<typeof globalThis.fetch>(async () => response.clone());
    // clone preserves the fixture's transport visibility explicitly.
    fetch.mockImplementation(async () => {
      const copy = response.clone(); Object.defineProperty(copy, "type", { value: "cors" }); return copy;
    });
    const error = await refusal(client(fetch)[path](REQUEST));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(view(error).dispatched).toBe("unknown");
  });
});

describe("authoritative response evidence parser", () => {
  it.each(["true", "false", " \ttrue\t ", " \tfalse\t "])("accepts exact ASCII dispatch %p", (value) => {
    const evidence = parse([["X-AgentCC-Dispatched", value], ["X-AgentCC-Request-ID", ID]]);
    expect(evidence).toEqual({ dispatched: value.includes("true"), gatewayRequestId: ID, clientRequestId: null });
  });
  it.each([[], [""], ["TRUE"], ["False"], ["1"], ["0"], ["true, true"], ["false, false"], ["true", "false"], ["false", "false"], [" false"], ["false\n"]].map((values) => ({ values })))("rejects dispatch multiset $values", ({ values }) => {
    expect(parse(values.map((value) => ["x-agentcc-dispatched", value] as const)).dispatched).toBe("unknown");
  });
  it.each(["", "offline", ID.toLowerCase(), "8" + ID.slice(1), "I" + ID.slice(1), ID.slice(1), ID + "0", ID + ", " + ID, " " + ID])("rejects invalid gateway identity %p without substitution", (id) => {
    const error = gateway.APIStatusError.from(503, { error: { metadata: { request_id: ID, dispatched: false } } }, new Headers({ "x-agentcc-request-id": id, "x-request-id": ID, "x-agentcc-client-request-id": ID }));
    // Fetch trims ordinary OWS; raw parser still validates the exact ULID field.
    if (!id.startsWith(" ")) expect(error.requestId).toBeNull();
    expect(parse([["x-agentcc-request-id", id]]).gatewayRequestId).toBeNull();
    expect(refusalRetry(503, error.body, error.headers)).toBe("never");
  });
  it("never substitutes legacy, client, or body identity for gateway identity", () => {
    const error = gateway.APIStatusError.from(403, { error: { code: "managed_model_unpriced", metadata: { request_id: ID, dispatched: false } } }, new Headers({ "x-request-id": ID, "x-agentcc-client-request-id": ID2 }));
    expect(error.requestId).toBeNull();
    expect(view(error).gatewayEvidence).toEqual({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: ID2 });
  });
  it("rejects duplicate IDs and known lossy adapter evidence", () => {
    expect(parse([["x-agentcc-request-id", ID], ["X-AgentCC-Request-ID", ID]]).gatewayRequestId).toBeNull();
    expect(parse(new Headers(HEADERS), { cardinalityObservable: false })).toEqual({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: null });
    expect(parse(undefined, { headersObservable: false })).toEqual({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: null });
  });
  it.each([null, [], { model: 2, candidates: ["first/model", 1] }, { model: [], candidates: "model" }].map((metadata) => ({ metadata })))("validates typed metadata without dropping raw $metadata", ({ metadata }) => {
    const error = gateway.APIStatusError.from(400, { error: { code: "managed_model_ambiguous", metadata } }, new Headers(HEADERS));
    expect(view(error).model).toBeNull(); expect(view(error).candidates).toBeNull();
    expect(error.body).toEqual({ error: { code: "managed_model_ambiguous", metadata } });
    expect(refusalRetry(400, error.body, error.headers)).toBe("never");
  });
  it.each(ROWS)("does not promote flat or status-mismatched $code", ({ status, code }) => {
    expect(gateway.APIStatusError.from(status, { code }, new Headers()).remedy).toBeNull();
    expect(gateway.APIStatusError.from(500, { error: { code } }, new Headers()).remedy).toBeNull();
    expect(refusalRetry(500, { error: { code } }, new Headers(HEADERS))).toBe("never");
  });
});

it("success, raw, and stream preserve initial evidence without trusting body mirrors", async () => {
  const body = { status: "failed", metadata: { dispatched: false, request_id: "provider" } };
  const response = new Response(JSON.stringify(body), { headers: { ...HEADERS, "x-agentcc-dispatched": "true" } });
  const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
  const result = await client(fetch).requestWithResponse(REQUEST);
  expect(view(result).gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "client-correlation" });
  expect(result.data).toMatchObject(body);
  expect(typeof api.getGatewayEvidence).toBe("function");
  expect(api.getGatewayEvidence!(response)).toBe(view(result).gatewayEvidence);
  response.headers.set("x-agentcc-dispatched", "false");
  expect(api.getGatewayEvidence!(response).dispatched).toBe(true);
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("stream partial output, error, and cancellation retain the owning snapshot", async () => {
  const payload = 'data: {"choices":[{"delta":{"content":"part"}}]}\n\ndata: {"error":{"code":"upstream_error","message":"stopped","metadata":{"dispatched":false,"request_id":"provider"}}}\n\n';
  const response = new Response(payload, { headers: { ...HEADERS, "x-agentcc-dispatched": "true", "content-type": "text/event-stream" } });
  const fetch = jest.fn<typeof globalThis.fetch>(async () => response);
  const stream = new gateway.Stream(await client(fetch).requestStream(REQUEST));
  const evidence = view(stream).gatewayEvidence;
  expect(evidence).toEqual({ dispatched: true, gatewayRequestId: ID, clientRequestId: "client-correlation" });
  response.headers.set("x-agentcc-dispatched", "false");
  const iterator = stream[Symbol.asyncIterator]();
  expect((await iterator.next()).value).toMatchObject({ choices: [{ delta: { content: "part" } }] });
  let caught: unknown;
  try { await iterator.next(); } catch (error) { caught = error; }
  expect(caught).toBeInstanceOf(gateway.StreamError);
  expect(view(caught).gatewayEvidence).toBe(evidence);
  stream.abort();
  expect(view(stream).gatewayEvidence).toBe(evidence);
  expect(fetch).toHaveBeenCalledTimes(1);
});
