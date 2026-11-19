/**
 * Platform request behavior: the four retry classes on the platform executor, the 409
 * in-progress wait, the sandboxes.kill 404-on-retry rule, Retry-After, abort, and redirects.
 */
import { validate as isUuid, version as uuidVersion } from "uuid";

import { CoreRateLimitError, CoreServerError, json, makeCore, netError, Script } from "../__fixtures__/platform";
import {
  APIConnectionError,
  APITimeoutError,
  ConfigurationError,
  IdempotencyKeyInProgressError,
  NotFoundError,
  PayloadTooLargeError,
  UnexpectedRedirectError,
} from "../errors";
import { counts, retryClassOf } from "../policy";
import { OPS } from "../__fixtures__/platform";

const IN_PROGRESS = { code: "idempotency_key_in_progress", message: "still running" };

describe("retry classes from the contract", () => {
  it("derives the class from the idempotency flags, else the method", () => {
    expect(retryClassOf(OPS["runs.create"]!)).toBe("keyed");
    expect(retryClassOf(OPS["environments.create"]!)).toBe("keyed-not-durable");
    expect(retryClassOf(OPS["runs.get"]!)).toBe("http-idempotent");
    expect(retryClassOf(OPS["sandboxes.kill"]!)).toBe("http-idempotent");
    expect(retryClassOf(OPS["sandboxes.create"]!)).toBe("unsafe");
    expect(counts(OPS)).toMatchObject({ keyed: 1, "keyed-not-durable": 1, stream: 1, paginated: 2 });
  });

  it.each([429, 502, 503, 504])("keyed retries %i with the same key on every attempt", async (status) => {
    const script = new Script([json(status), json(status), json(201, { id: "c1" })]);
    const { data, meta } = await makeCore(script)
      .call("runs.create", { body: { agentId: "a" } })
      .withResponse();
    expect(data).toEqual({ id: "c1" });
    const key = script.keys[0]!;
    expect(isUuid(key) && uuidVersion(key) === 4).toBe(true);
    expect(script.keys).toEqual([key, key, key]);
    expect(meta.idempotencyKey).toBe(key);
    expect(meta.attempts).toBe(3);
  });

  it("keyed takes the caller's key and an unkeyed operation refuses one", async () => {
    const script = new Script([json(201, {})]);
    await makeCore(script).call("runs.create", { body: {} }, { idempotencyKey: "ci-abc123" });
    expect(script.keys).toEqual(["ci-abc123"]);
    await expect(makeCore(script).call("sandboxes.create", { body: {} }, { idempotencyKey: "ci-abc123" })).rejects.toThrow(
      ConfigurationError,
    );
    await expect(makeCore(script).call("runs.create", { body: {} }, { idempotencyKey: "has space" })).rejects.toThrow(ConfigurationError);
    expect(script.requests).toHaveLength(1);
  });

  it("a keyed 409 in progress waits for Retry-After, then 1 s, and resends the same key", async () => {
    const script = new Script([json(409, IN_PROGRESS, { "retry-after": "2" }), json(409, IN_PROGRESS), json(201, { id: "c1" })]);
    const { meta } = await makeCore(script).call("runs.create", { body: {} }).withResponse();
    expect(script.sleeps).toEqual([2000, 1000]);
    expect(new Set(script.keys).size).toBe(1);
    expect(meta.attempts).toBe(3);
  });

  it("a 409 in progress past the wait cap, or on an unkeyed call, throws", async () => {
    const script = new Script([json(409, IN_PROGRESS, { "retry-after": "600" })]);
    const err = await makeCore(script)
      .call("runs.create", { body: {} })
      .then(
        () => undefined,
        (e: unknown) => e,
      );
    expect(err).toBeInstanceOf(IdempotencyKeyInProgressError);
    expect((err as IdempotencyKeyInProgressError).retryAfter).toBe(600);
    expect((err as IdempotencyKeyInProgressError).idempotencyKey).toBe(script.keys[0]);
    const unkeyed = new Script([json(409, IN_PROGRESS)]);
    await expect(makeCore(unkeyed).call("sandboxes.create", { body: {} })).rejects.toThrow(IdempotencyKeyInProgressError);
    expect(unkeyed.requests).toHaveLength(1);
  });

  it.each([500, 502, 503, 504])("keyed-not-durable never retries %i", async (status) => {
    const script = new Script([json(status), json(201, {})]);
    await expect(makeCore(script).call("environments.create", { body: {} })).rejects.toThrow(CoreServerError);
    expect(script.requests).toHaveLength(1);
  });

  it("keyed-not-durable retries 429 and pre-send errors with the same key, not a lost connection", async () => {
    const script = new Script([netError("ECONNREFUSED"), json(429, undefined, { "retry-after": "0" }), json(201, { id: "e1" })]);
    await expect(makeCore(script).call("environments.create", { body: {} })).resolves.toEqual({ id: "e1" });
    expect(script.requests).toHaveLength(3);
    expect(new Set(script.keys).size).toBe(1);
    const lost = new Script([netError("ECONNRESET"), json(201, {})]);
    const err = await makeCore(lost)
      .call("environments.create", { body: {} })
      .then(
        () => undefined,
        (e: unknown) => e,
      );
    expect(err).toBeInstanceOf(APIConnectionError);
    expect((err as APIConnectionError).possiblyApplied).toBe(true);
    expect(lost.requests).toHaveLength(1);
  });

  it.each([502, 503, 504])("http-idempotent retries %i; a 500 is not retried", async (status) => {
    const script = new Script([json(status), json(200, { id: "c1" })]);
    await expect(makeCore(script).call("runs.get", { path: { id: "c1" } })).resolves.toEqual({ id: "c1" });
    expect(script.keys).toEqual([null, null]);
    const five = new Script([json(500), json(200, {})]);
    await expect(makeCore(five).call("runs.get", { path: { id: "c1" } })).rejects.toThrow(CoreServerError);
    expect(five.requests).toHaveLength(1);
  });

  it.each([500, 502, 503, 504])("unsafe never retries %i (sandboxes.create makes one attempt)", async (status) => {
    const script = new Script([json(status), json(201, {})]);
    await expect(makeCore(script).call("sandboxes.create", { body: {} })).rejects.toThrow(CoreServerError);
    expect(script.requests).toHaveLength(1);
  });

  it("unsafe retries 429 and pre-send connect errors only", async () => {
    const script = new Script([json(429), netError("ECONNREFUSED"), json(201, { id: "s1" })]);
    await expect(makeCore(script).call("sandboxes.create", { body: {} })).resolves.toEqual({ id: "s1" });
    expect(script.requests).toHaveLength(3);
    for (const after of [netError("ECONNRESET"), netError("UND_ERR_SOCKET")]) {
      const s = new Script([after, json(201, {})]);
      await expect(makeCore(s).call("sandboxes.create", { body: {} })).rejects.toThrow(APIConnectionError);
      expect(s.requests).toHaveLength(1);
    }
  });

  it("a 404 on a retry of sandboxes.kill is success; on the first attempt or after a 429 it is not", async () => {
    for (const first of [netError("ECONNRESET"), json(503)]) {
      const script = new Script([first, json(404, { code: "not_found" })]);
      const { data, meta } = await makeCore(script)
        .call("sandboxes.kill", { path: { id: "sb1" } })
        .withResponse();
      expect(data).toBeUndefined();
      expect(meta.alreadyApplied).toBe(true);
      expect(meta.attempts).toBe(2);
    }
    for (const answers of [[json(404, { code: "not_found" })], [json(429), json(404, { code: "not_found" })]]) {
      await expect(makeCore(new Script(answers)).call("sandboxes.kill", { path: { id: "sb1" } })).rejects.toThrow(NotFoundError);
    }
    await expect(makeCore(new Script([json(503), json(404, {})])).call("runs.get", { path: { id: "c" } })).rejects.toThrow(NotFoundError);
  });

  it("honours Retry-After and bounds the retries", async () => {
    const script = new Script([json(429, undefined, { "retry-after": "3" }), json(200, {})]);
    await makeCore(script, { backoffBaseMs: 0 }).call("runs.get", { path: { id: "c1" } });
    expect(script.sleeps).toEqual([3000]);
    const spent = new Script([json(429, { error: "omega_rate_limited", requestId: "r-1" }, { "retry-after": "1" })]);
    const err = (await makeCore(spent, { retries: 2 })
      .call("runs.get", { path: { id: "c1" } })
      .then(undefined, (e: unknown) => e)) as CoreRateLimitError;
    expect(err).toBeInstanceOf(CoreRateLimitError);
    expect(spent.requests).toHaveLength(3);
    expect([err.retryAfter, err.requestId, err.code]).toEqual([1, "r-1", "omega_rate_limited"]);
    const once = new Script([json(503)]);
    await expect(makeCore(once).call("runs.get", { path: { id: "c1" } }, { retries: 0 })).rejects.toThrow(CoreServerError);
    expect(once.requests).toHaveLength(1);
  });

  it("a timeout is APITimeoutError and an abort ends the call without retrying", async () => {
    const slow = new Script([
      (req) => new Promise<Response>((_, reject) => req.signal.addEventListener("abort", () => reject(req.signal.reason))),
    ]);
    const err = await makeCore(slow, { retries: 0 })
      .call("runs.get", { path: { id: "c" } }, { timeoutMs: 20 })
      .then(undefined, (e: unknown) => e);
    expect(err).toBeInstanceOf(APITimeoutError);
    const controller = new AbortController();
    const hang = new Script([
      (req) => new Promise<Response>((_, reject) => req.signal.addEventListener("abort", () => reject(req.signal.reason))),
    ]);
    const pending = makeCore(hang).call("runs.get", { path: { id: "c" } }, { signal: controller.signal });
    setTimeout(() => controller.abort(new Error("stop now")), 10);
    await expect(pending).rejects.toThrow("stop now");
    expect(hang.requests).toHaveLength(1);
  });
});

describe("requests", () => {
  it("never follows a redirect, and the keys never reach the target (acceptance 5)", async () => {
    const script = new Script([new Response(null, { status: 302, headers: { location: "https://evil.example:8443/steal?k=1" } })]);
    const err = (await makeCore(script)
      .call("platform.capabilities.get")
      .then(undefined, (e: unknown) => e)) as UnexpectedRedirectError;
    expect(err).toBeInstanceOf(UnexpectedRedirectError);
    expect(err.targetHost).toBe("evil.example:8443");
    expect(err.message).not.toContain("steal");
    expect(script.requests).toHaveLength(1);
    expect(new URL(script.requests[0]!.url).host).toBe("api.futureagi.com");
    expect(script.requests[0]!.redirect).toBe("manual");
  });

  it("refuses human-only verbs, undeclared headers and an oversized body before sending", async () => {
    const script = new Script([json(200, {})]);
    await expect(makeCore(script).call("approvals.decide", { path: { id: "a" }, body: {} })).rejects.toThrow(ConfigurationError);
    await expect(makeCore(script).call("runs.get", { path: { id: "c" } }, { headers: { "X-Api-Key": "x" } })).rejects.toThrow(
      ConfigurationError,
    );
    const big = await makeCore(script)
      .call("runs.create", { body: { x: "a".repeat(1024 * 1024) } })
      .then(undefined, (e: unknown) => e);
    expect(big).toBeInstanceOf(PayloadTooLargeError);
    expect((big as PayloadTooLargeError).local).toBe(true);
    expect(script.requests).toHaveLength(0);
  });

  it("sends the credential, encodes path segments and only declared query keys", async () => {
    const script = new Script([json(200, {})]);
    await makeCore(script).call("runs.get", { path: { id: "a/b c" } });
    await makeCore(script).call("files.write", { path: { id: "s1", path: "dir/a b.txt" }, body: new Uint8Array([1, 2]) });
    const [get, put] = script.requests;
    expect(get!.url).toBe("https://api.futureagi.com/omega/api/workspace/conversations/a%2Fb%20c");
    expect(get!.headers.get("x-api-key")).toBe("k-test-1234");
    expect(get!.headers.get("idempotency-key")).toBeNull();
    expect(put!.url).toBe("https://api.futureagi.com/omega/api/workspace/sandboxes/s1/files/dir/a%20b.txt");
    expect(put!.headers.get("content-type")).toBe("application/octet-stream");
    await expect(makeCore(script).call("runs.list", { query: { apiKey: "x" } })).rejects.toThrow(ConfigurationError);
    await expect(makeCore(script).call("runs.get", { path: { id: ".." } })).rejects.toThrow(ConfigurationError);
  });

  it("in Bearer mode sends only the token, never the key headers", async () => {
    const script = new Script([json(200, {})]);
    const core = makeCore(script, {
      resolveOrigin: () => ({
        url: new URL("http://127.0.0.1:9"),
        base: "http://127.0.0.1:9",
        mode: "bearer",
        source: "env",
        custom: false,
        headers: { Authorization: "Bearer ee-token-123456" },
        secrets: ["ee-token-123456"],
      }),
    });
    await core.call("platform.capabilities.get");
    const sent = script.requests[0]!;
    expect(sent.headers.get("authorization")).toBe("Bearer ee-token-123456");
    expect(sent.headers.has("x-api-key")).toBe(false);
    expect(sent.headers.has("x-secret-key")).toBe(false);
  });
});
