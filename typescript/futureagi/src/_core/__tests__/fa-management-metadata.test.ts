import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../errors";

const headers = {
  "X-Request-Id": "trace-fixture-id",
  "X-Upstream-Request-Id": "upstream-fixture-id",
  "X-Omega-Receipt-Id": "receipt-fixture-id",
  "Retry-After": "9",
};
const cases = [200, 400].flatMap(status => [false, "error", "failed"].flatMap(envelopeStatus =>
  [false, true].flatMap(raw => [false, true].map(copy => ({ status, envelopeStatus, raw, copy })))));

it.each(cases)("preserves error metadata: HTTP $status / $envelopeStatus raw=$raw copy=$copy", async ({ status, envelopeStatus, raw, copy }) => {
  const secret = "private-value-fixture";
  const body = { credentials: { password: secret } };
  const payload = { status: envelopeStatus, result: {
    error_code: "validation_failed", message: `Rejected ${secret}`,
    diagnostic: secret, details: [{ [secret]: secret }],
  } };
  const transport = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init);
    expect(request.method).toBe("POST");
    expect(new URL(request.url).pathname).toBe("/agentcc/provider-credentials/provider/rotate/");
    expect(await request.json()).toEqual(body);
    return Response.json(payload, { status, headers });
  });
  const client = new FutureAGIClient({ apiKey: "api-fixture", secretKey: "secret-fixture",
    baseUrl: "http://localhost:9012", retries: 0, fetch: transport as typeof fetch });
  const target = copy ? client.withOptions({ retries: 0 }) : client;
  const call = target.gateway.providerCredentials.rotate("provider", body);
  const error = await (raw ? call.withResponse() : call).then(
    () => { throw new Error("Expected typed error"); }, (e: unknown) => e,
  );
  expect(transport).toHaveBeenCalledTimes(1);
  expect(error).toBeInstanceOf(BadRequestError);
  const typed = error as BadRequestError;
  expect(typed.payload).toEqual({ status: envelopeStatus, result: {
    error_code: "validation_failed", message: "Rejected [redacted]",
    diagnostic: "[redacted]", details: [{ [secret]: "[redacted]" }],
  } });
  expect(typed.statusCode).toBe(400);
  expect(typed.code).toBe("validation_failed");
  expect(typed.operation).toBe("gateway.provider_credentials.rotate");
  expect(String(typed)).not.toContain(secret);
  expect({ requestId: typed.requestId, upstreamRequestId: typed.upstreamRequestId,
    receiptId: typed.receiptId, retryAfter: typed.retryAfter }).toEqual({
    requestId: headers["X-Request-Id"], upstreamRequestId: headers["X-Upstream-Request-Id"],
    receiptId: headers["X-Omega-Receipt-Id"], retryAfter: 9,
  });
  expect(payload.result.diagnostic).toBe(secret);
});
