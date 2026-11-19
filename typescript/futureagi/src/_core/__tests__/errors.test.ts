/**
 * Platform error mapping: every status raises the same class as Python's
 * fi.errors; codes pick narrower classes; secrets never reach an error; connection failures and
 * timeouts are APIConnectionError / APITimeoutError. The core-namespace half is core-errors.test.ts.
 */
import { SDKException } from "../../utils/errors";
import { CoreServerError, json, makeCore, netError, Script, STATUS_CLASSES } from "../__fixtures__/platform";
import { apiError, errorClassFor, parseRetryAfter, readErrorShape } from "../error-map";
import * as E from "../errors";

describe("the status mapping", () => {
  it.each(STATUS_CLASSES)("%i is %p on a platform namespace", async (status, cls) => {
    // A bare Django 404 is not an EE resource error; it is diagnosed separately.
    const body = status === 404 ? { code: "not_found", message: "nope" } : { detail: "nope" };
    const script = new Script([json(status, body, { "x-request-id": "req-7" })]);
    const err = (await makeCore(script, { retries: 0 })
      .call("platform.capabilities.get")
      .then(undefined, (e: unknown) => e)) as E.FutureAGIAPIError;
    expect(err.constructor).toBe(cls);
    expect([err.statusCode, err.requestId]).toEqual([status, "req-7"]);
    expect(err).toBeInstanceOf(SDKException);
    expect(err).toBeInstanceOf(E.FutureAGIAPIError);
  });

  it("known codes pick narrower classes inside their own status family only", () => {
    expect(errorClassFor(404, "product_not_admitted")).toBe(E.ProductNotAvailableError);
    expect(errorClassFor(409, "idempotency_key_in_progress")).toBe(E.IdempotencyKeyInProgressError);
    expect(errorClassFor(422, "idempotency_key_reused")).toBe(E.IdempotencyKeyReusedError);
    expect(errorClassFor(500, "product_not_admitted")).toBe(CoreServerError);
    expect(errorClassFor(409, undefined, "sandboxes")).toBe(E.SandboxStateError);
    expect(E.isAuthError(new E.AuthenticationError(401, null))).toBe(true);
  });

  it("reads the gateway, EE and Hub shapes, and ignores sentences posing as codes", () => {
    expect(readErrorShape({ error: "omega_rate_limited", requestId: "g-1", retryAfterSeconds: 4 })).toMatchObject({
      code: "omega_rate_limited",
      requestId: "g-1",
      retryAfter: 4,
    });
    expect(readErrorShape({ code: "conflict", message: "busy", request_id: "ee-1" })).toMatchObject({
      code: "conflict",
      message: "busy",
      upstreamRequestId: "ee-1",
    });
    expect(readErrorShape({ error: { code: "omega_hub_x", message: "m", fix: "do y" } })).toMatchObject({
      code: "omega_hub_x",
      hint: "do y",
    });
    expect(readErrorShape({ error: "Something went wrong here" })).toEqual({});
    expect(parseRetryAfter("Wed, 21 Oct 2015 07:28:00 GMT")).toBe(0);
    expect(parseRetryAfter("2.5")).toBe(2.5);
  });

  it("words platform errors with the operation and redacts and scrubs", async () => {
    const echo = { code: "bad_request", message: "bad key k-test-1234 / s-test-1234", detail: { token: "t-123456" } };
    const err = (await makeCore(new Script([json(400, echo)]))
      .call("platform.capabilities.get")
      .then(undefined, (e: unknown) => e)) as E.BadRequestError;
    const text = `${err.message} ${JSON.stringify(err.payload)} ${JSON.stringify(err)}`;
    expect(text).not.toMatch(/k-test-1234|s-test-1234|t-123456/u);
    expect(err.message.startsWith("platform.capabilities.get failed with status 400 (bad_request)")).toBe(true);
    expect(err.toJSON()).toMatchObject({ errorCode: "BAD_REQUEST", code: "bad_request" });
    expect(JSON.stringify(err.toJSON())).not.toContain("payload");
  });

  it("a non-JSON body is classified by status and never echoed", async () => {
    const script = new Script([new Response("<html>secret page</html>", { status: 503 })]);
    const err = (await makeCore(script, { retries: 0 })
      .call("platform.capabilities.get")
      .then(undefined, (e: unknown) => e)) as CoreServerError;
    expect(err).toBeInstanceOf(CoreServerError);
    expect(err.message).not.toContain("secret page");
  });

  it("copies body fields onto a core error so e.detail keeps working", () => {
    const err = apiError(404, { detail: "Not found." }, new Headers(), { assignBody: true }) as E.NotFoundError & { detail?: string };
    expect(err).toBeInstanceOf(E.NotFoundError);
    expect(err.detail).toBe("Not found.");
  });
});

describe("no response", () => {
  it.each([
    ["ECONNREFUSED", E.APIConnectionError, false],
    ["ENOTFOUND", E.APIConnectionError, false],
    ["UND_ERR_CONNECT_TIMEOUT", E.APITimeoutError, false],
    ["ECONNRESET", E.APIConnectionError, true],
  ] as const)("%s is %p (possiblyApplied %p)", async (code, cls, applied) => {
    const script = new Script([netError(code)]);
    const err = (await makeCore(script, { retries: 0 })
      .call("platform.capabilities.get")
      .then(undefined, (e: unknown) => e)) as E.APIConnectionError;
    expect(err.constructor).toBe(cls);
    expect(err).toBeInstanceOf(E.TransportError);
    expect(err.possiblyApplied).toBe(applied);
  });
});
