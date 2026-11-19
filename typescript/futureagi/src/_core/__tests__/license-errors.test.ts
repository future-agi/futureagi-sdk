import fs from "node:fs";
import path from "node:path";
import * as E from "../errors";
import * as Public from "../../index";
import * as Legacy from "../../utils/errors";
import { apiError, errorClassFor } from "../error-map";
import { FutureAGIClient } from "../../futureagi-client";

const root = path.resolve(__dirname, "../../../../..");
const body = JSON.parse(fs.readFileSync(path.join(root, "python/tests/fixtures/license_missing.json"), "utf8")).body;
const classNamed = (name: string) => (E as unknown as Record<string, typeof E.FutureAGIAPIError>)[name];
const source = (name: string) => fs.readFileSync(path.join(root, "typescript/futureagi/src", name), "utf8");
function docBefore(text: string, marker: string): string {
  const at = text.indexOf(marker);
  expect(at).toBeGreaterThan(-1);
  const prefix = text.slice(0, at);
  return prefix.slice(prefix.lastIndexOf("/**"));
}

it.each([undefined, "tracing.issues"])("recorded LICENSE_MISSING is typed and actionable (%s)", (operation) => {
  const err = apiError(402, body, new Headers({ "x-request-id": "req-license" }), { operation });
  expect(err.constructor.name).toBe("LicenseRequiredError");
  expect(err).toBeInstanceOf(classNamed("PaymentRequiredError"));
  expect(err).toBeInstanceOf(E.FutureAGIAPIError);
  expect([err.statusCode, err.code, err.requestId]).toEqual([402, "LICENSE_MISSING", "req-license"]);
  expect(err.payload).toEqual(body);
  expect(err.getErrorCode()).toBe("LICENSE_REQUIRED");
  expect(err.message).toContain("Enterprise licence on this server");
  expect(err.message).toContain("LICENSE_MISSING");
  expect(err.message).toContain("Feature 'error_feed' needs");
  expect(err.message).not.toContain("Upgrade your plan");
  expect(err.message.toLowerCase()).not.toContain("hosted");
  if (operation) expect(err.message).toContain(operation);
  expect(err.toJSON().name).toBe("LicenseRequiredError");
});

describe.each(["nested", "top", "result"])("license feature in %s envelope", (envelope) => {
  it.each([
    [{ feature: "error_feed" }, "Feature 'error_feed'"],
    [{ feature: "  error_\nfeed  " }, "Feature 'error_ feed'"],
    [{ feature: "x".repeat(600) }, `Feature '${"x".repeat(500)}...'`],
    [{ feature: "" }, "This feature"],
    [{ feature: 42 }, "This feature"],
    [{}, "This feature"],
    [null, "This feature"],
    ["not an object", "This feature"],
  ])("names only valid bounded features (%j)", (detail, subject) => {
    const error = { code: "LICENSE_MISSING", detail };
    const payload = envelope === "nested" ? { error } : envelope === "result" ? { status: false, result: { error } } : error;
    const err = apiError(402, payload);
    expect(err.message).toContain(`${subject} needs an Enterprise licence on this server`);
    expect(err.message).not.toContain("\n");
    expect(err.payload).toEqual(payload);
  });
});

it("shared contract records the payment-required status family", () => {
  const contracts = JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures/contracts/operations.json"), "utf8"));
  expect(contracts.status_classes["402"]).toBe("PaymentRequiredError");
  expect(contracts.fa_codes.payment_required).toBe(402);
});

it.each([null, { code: "unknown_payment" }, { code: "ENTITLEMENT_DENIED" }])("other 402 stays payment-required (%j)", (payload) => {
  const err = apiError(402, payload);
  expect(err.constructor.name).toBe("PaymentRequiredError");
  expect(err).toBeInstanceOf(E.FutureAGIAPIError);
  expect(err.getErrorCode()).toBe("PAYMENT_REQUIRED");
  expect(err.code).toBe(payload?.code ?? "http_402");
});

it.each([
  [400, "BadRequestError"], [401, "AuthenticationError"], [403, "PermissionDeniedError"],
  [404, "NotFoundError"], [409, "ConflictError"], [413, "PayloadTooLargeError"],
  [418, "FutureAGIAPIError"], [422, "UnprocessableEntityError"], [429, "CoreRateLimitError"],
  [500, "CoreServerError"], [503, "CoreServerError"],
] as const)("LICENSE_MISSING cannot escape 402 into %i", (status, name) => {
  expect(errorClassFor(status, "LICENSE_MISSING").name).toBe(name);
  expect(errorClassFor(status).name).toBe(name);
});

it.each([
  [404, "product_not_admitted", "ProductNotAvailableError"],
  [409, "idempotency_key_in_progress", "IdempotencyKeyInProgressError"],
  [422, "idempotency_key_reused", "IdempotencyKeyReusedError"],
] as const)("existing code mapping stays unchanged: %s %s", (status, code, name) => {
  expect(errorClassFor(status, code).name).toBe(name);
  expect(errorClassFor(402, code).name).toBe("PaymentRequiredError");
});

it("new errors are public exports", () => {
  for (const name of ["PaymentRequiredError", "LicenseRequiredError"]) {
    expect(classNamed(name)).toBeDefined();
    expect((Public as unknown as Record<string, unknown>)[name]).toBe(classNamed(name));
  }
});

it("tracing transport throws LicenseRequiredError without retry", async () => {
  const requests: string[] = [];
  const fetchMock = (async (input: RequestInfo | URL, init?: RequestInit) => {
    requests.push(new Request(input as RequestInfo, init).url);
    return new Response(JSON.stringify(body), { status: 402, headers: { "content-type": "application/json" } });
  }) as typeof fetch;
  const c = new FutureAGIClient({ apiKey: "k-test-1234", secretKey: "s-test-1234", baseUrl: "http://api.test", fetch: fetchMock });
  const err = await c.tracing.issues().then(() => undefined, (e: unknown) => e);
  expect(err).toBeInstanceOf(E.FutureAGIAPIError);
  expect((err as Error).constructor.name).toBe("LicenseRequiredError");
  expect(requests).toEqual(["http://api.test/tracer/feed/issues/"]);
});

it.each(["issues", "issue", "issueStats"])("public licensed docs: %s", (method) => {
  const doc = docBefore(source("generated/tracing.ts"), `  ${method}(`);
  expect(doc).toContain("Enterprise licence");
  expect(doc).toContain("LicenseRequiredError");
  expect(doc).toContain("self-hosted");
  expect(doc).toContain("cloud plan");
});

it.each([
  "listErrorFeedIssues", "getErrorFeedIssue", "getErrorFeedIssueStats",
  "tracerFeedIssuesPartialUpdate", "tracerFeedIssuesCreateLinearIssueCreate",
  "tracerFeedIssuesDeepAnalysisCreate", "tracerFeedIssuesOverviewList",
  "tracerFeedIssuesRedirectList", "tracerFeedIssuesRootCauseList",
  "tracerFeedIssuesSidebarList", "tracerFeedIssuesTracesList", "tracerFeedIssuesTrendsList",
])("generated licensed docs: %s", (method) => {
  const doc = docBefore(source("generated/openapi/sdk.gen.ts"), `export const ${method} =`);
  expect(doc).toContain("Enterprise licence");
  expect(doc).toContain("LicenseRequiredError");
});

it.each(["addDatasetUserEval", "editAndRunDatasetUserEval"])("conditional Turing gate docs: %s", (method) => {
  const doc = docBefore(source("futureagi-client.ts"), `  ${method}(`);
  expect(doc).toContain("Enterprise licence");
  expect(doc).toContain("Turing/Protect");
  expect(doc).toContain("PaymentRequiredError");
  expect(doc).toContain("ENTITLEMENT_DENIED");
});

it("legacy dataset conditional Turing gate docs", () => {
  const doc = docBefore(source("datasets/dataset.ts"), "    async addEvaluation(");
  for (const wording of ["Enterprise licence", "Turing/Protect", "ENTITLEMENT_DENIED",
    "DatasetError", "PaymentRequiredError", "FutureAGIClient", "Code evaluations"]) {
    expect(doc).toContain(wording);
  }
});

// Every error declared by @future-agi/sdk 0.1.2 dist/esm/utils/errors.d.ts.
it("all published 0.1.2 error names remain", () => {
  const names = `SDKException DatasetError DatasetNotFoundError DatasetAuthError
DatasetValidationError RateLimitError ServerError ServiceUnavailableError MissingAuthError
InvalidAuthError TemplateNotFound InvalidAdditionalHeaders InvalidNumberOfEmbeddings
InvalidValueType InvalidSupportedType MissingRequiredKey MissingRequiredConfigForEvalTemplate
FileNotFoundException UnsupportedFileType TemplateAlreadyExists`.split(/\s+/u);
  for (const name of names) {
    expect(typeof (Legacy as unknown as Record<string, unknown>)[name]).toBe("function");
    expect(typeof (Public as unknown as Record<string, unknown>)[name]).toBe("function");
  }
});

it.each(["modelHubDevelopsAddUserEvalCreate", "modelHubDevelopsEditAndRunUserEvalCreate"])("generated conditional gate docs: %s", (method) => {
  const doc = docBefore(source("generated/openapi/sdk.gen.ts"), `export const ${method} =`);
  expect(doc).toContain("Enterprise licence");
  expect(doc).toContain("Turing/Protect");
  expect(doc).toContain("PaymentRequiredError");
  expect(doc).toContain("ENTITLEMENT_DENIED");
});
