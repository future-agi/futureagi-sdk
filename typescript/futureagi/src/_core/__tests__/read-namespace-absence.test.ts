import { FutureAGIClient } from "../../futureagi-client";

const client = new FutureAGIClient({
  apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9031",
  fetch: (async () => { throw new Error("absence checks must not send a request"); }) as typeof fetch,
});

test.each(["billing", "keys", "usage"])("unqualified %s namespace is absent from clients and copies", name => {
  expect(name in client).toBe(false);
  expect(name in client.withOptions({ timeoutMs: 1000 })).toBe(false);
});
