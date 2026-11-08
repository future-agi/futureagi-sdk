import * as Public from "../../index";
import { FutureAGIClient } from "../../futureagi-client";
import { apiError } from "../error-map";
import * as E from "../errors";

// Synthetic local responses exercise the merged mapper through the real Console executor.
const apiKey = "composition-api-key";
const secretKey = "composition-secret-key";
const env = { ...process.env };
beforeEach(() => {
  for (const key of Object.keys(process.env)) if (key.startsWith("FI_")) delete process.env[key];
});
afterEach(() => { process.env = { ...env }; });

function make(answer: () => Response) {
  const fetch_ = jest.fn(async () => answer());
  const client = new FutureAGIClient({ apiKey, secretKey, baseUrl: "https://api.futureagi.com", retries: 2, fetch: fetch_ });
  return { client, fetch_ };
}

async function failure(call: PromiseLike<unknown>): Promise<E.FutureAGIAPIError> {
  return call.then(() => { throw new Error("expected HTTP failure"); }, (error: unknown) => {
    expect(error).toBeInstanceOf(E.FutureAGIAPIError);
    return error as E.FutureAGIAPIError;
  });
}

function envelope(code: string, shape: string): unknown {
  const error = { code, message: `denied ${secretKey}`, detail: { feature: `error_feed ${apiKey}`, api_key: secretKey } };
  if (shape === "nested") return { detail: "denied", error };
  if (shape === "result") return { status: false, result: { error } };
  return error;
}

const cases = [
  [402, "LICENSE_MISSING", E.LicenseRequiredError],
  [402, "ENTITLEMENT_DENIED", E.PaymentRequiredError],
  [402, "product_not_admitted", E.PaymentRequiredError],
  [404, "LICENSE_MISSING", E.NotFoundError],
  [404, "product_not_admitted", E.ProductNotAvailableError],
  [410, "LICENSE_MISSING", E.FutureAGIAPIError],
] as const;

describe.each(["top", "nested", "result"])("%s envelope", (shape) => {
  test.each(cases)("%i %s keeps its status family and scrubs feature text", async (status, code, expected) => {
    const { client, fetch_ } = make(() => new Response(JSON.stringify(envelope(code, shape)), {
      status, headers: { "x-request-id": "composition-request" },
    }));
    const error = await failure(client.agents.get("missing-id"));
    expect(error.constructor).toBe(expected);
    expect([error.statusCode, error.code, error.requestId]).toEqual([status, code, "composition-request"]);
    expect((error as E.FutureAGIAPIError & { cause?: unknown }).cause).toBeUndefined();
    expect(error.message).not.toContain("Console API is not available");
    for (const text of [String(error), JSON.stringify(error.payload), JSON.stringify(error.toJSON())]) {
      expect(text).not.toContain(apiKey);
      expect(text).not.toContain(secretKey);
    }
    if (expected === E.LicenseRequiredError) {
      expect(error).toBeInstanceOf(E.PaymentRequiredError);
      expect(error.message).toContain("error_feed");
      expect(error.message).toContain("Enterprise licence on this server");
      expect(error.message.toLowerCase()).not.toContain("hosted");
    } else {
      expect(error.message).not.toContain("Enterprise licence on this server");
    }
    expect(fetch_).toHaveBeenCalledTimes(1); // no preflight or retry despite nonzero retry budget
  });
});

test("availability diagnosis does not stick to later license responses", async () => {
  const responses = [
    new Response(`<html>${secretKey}</html>`, { status: 404, headers: { "x-request-id": apiKey } }),
    new Response(JSON.stringify(envelope("LICENSE_MISSING", "nested")), { status: 402 }),
    new Response(JSON.stringify(envelope("LICENSE_MISSING", "result")), { status: 404 }),
    new Response(JSON.stringify({ code: "ENTITLEMENT_DENIED" }), { status: 402 }),
  ];
  const { client, fetch_ } = make(() => {
    const response = responses.shift();
    if (response === undefined) throw new Error("unexpected extra request");
    return response;
  });
  const expected = [E.ConsoleUnavailableError, E.LicenseRequiredError, E.NotFoundError, E.PaymentRequiredError];
  for (const [index, ctor] of expected.entries()) {
    const error = await failure(client.agents.get("missing-id"));
    expect(error.constructor).toBe(ctor);
    const rendered = error.message + JSON.stringify(error.toJSON());
    for (const forbidden of [apiKey, secretKey, "<html>"]) expect(rendered).not.toContain(forbidden);
    expect(rendered.includes("Console API is not available")).toBe(ctor === E.ConsoleUnavailableError);
    expect(fetch_).toHaveBeenCalledTimes(index + 1);
  }
});

test.each([[402, E.LicenseRequiredError], [404, E.NotFoundError]] as const)(
  "core mapping of %i requires Console executor evidence", (status, expected) => {
    const body = { code: "LICENSE_MISSING", detail: { feature: "error_feed" } };
    const error = apiError(status, body);
    expect(error.constructor).toBe(expected);
    expect(error.payload).toBe(body);
    expect(error.code).toBe("LICENSE_MISSING");
    expect(apiError(402, body, undefined, { consoleUnavailableMessage: "must not replace a 402" }).constructor).toBe(E.LicenseRequiredError);
  },
);

test("both donor error exports remain identical", () => {
  expect(Public.PaymentRequiredError).toBe(E.PaymentRequiredError);
  expect(Public.LicenseRequiredError).toBe(E.LicenseRequiredError);
  expect(Public.ConsoleUnavailableError).toBe(E.ConsoleUnavailableError);
  expect(new Public.LicenseRequiredError(402, undefined)).toBeInstanceOf(E.PaymentRequiredError);
  expect(new Public.ConsoleUnavailableError(404, undefined)).toBeInstanceOf(E.NotFoundError);
});
