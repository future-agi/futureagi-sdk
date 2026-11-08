import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../errors";
import { PlatformCore, PlatformShared } from "../platform-base";

// Inspect identity as well as fetch calls: identical fetch functions alone do
// not prove that option copies share the origin and management state.
function state(client: FutureAGIClient) {
  return client as unknown as { managementShared: PlatformShared; managementCore?: PlatformCore };
}

const cases = [false, true].flatMap(warm => [200, 400].flatMap(status =>
  [false, true].map(raw => ({ warm, status, raw }))));

it.each(cases)("shares management state before and after first use: warm=$warm HTTP $status raw=$raw", async ({ warm, status, raw }) => {
  const transport = jest.fn(async () => Response.json({ status: false, result: {
    error_code: "validation_failed", message: "denied",
  } }, { status, headers: { "X-Request-Id": "trace-fixture-id", "Retry-After": "9" } }));
  const parent = new FutureAGIClient({ apiKey: "api-fixture", secretKey: "secret-fixture",
    baseUrl: "http://localhost:9012", retries: 0, fetch: transport as typeof fetch });
  expect(state(parent).managementCore).toBeUndefined();
  if (warm) void parent.gateway;
  const shared = state(parent).managementShared;
  const copy = parent.withOptions({ timeoutMs: 7000, retries: 0 });
  const sibling = parent.withOptions({ timeoutMs: 11000, retries: 0 });
  const nested = copy.withOptions({ retries: 0 });
  expect(transport).not.toHaveBeenCalled();
  for (const client of [copy, sibling, nested, parent]) {
    expect(state(client).managementShared).toBe(shared);
    const call = client.gateway.config.getActive();
    const error = await (raw ? call.withResponse() : call).then(
      () => { throw new Error("Expected typed error"); }, (e: unknown) => e,
    );
    expect(error).toBeInstanceOf(BadRequestError);
    expect(error).toMatchObject({ requestId: "trace-fixture-id", retryAfter: 9, statusCode: 400 });
    expect(state(client).managementCore!.shared).toBe(shared);
  }
  expect(transport).toHaveBeenCalledTimes(4);
  expect(state(copy).managementCore).not.toBe(state(parent).managementCore);
  expect(state(copy).managementCore!.settings.timeoutMs).toBe(7000);
  expect(state(sibling).managementCore!.settings.timeoutMs).toBe(11000);
  expect(state(nested).managementCore!.settings.timeoutMs).toBe(7000);
  expect(state(parent).managementCore!.settings.timeoutMs).toBe(30000);
});
