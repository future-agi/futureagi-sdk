import { inspect } from "node:util";
import { FutureAGIClient } from "../futureagi-client";

it("keeps configured headers private on client copies without dropping them from requests", async () => {
  const saved = process.env.FI_EXTRA_HEADERS;
  delete process.env.FI_EXTRA_HEADERS;
  try {
    const seen: Request[] = [];
    const transport: typeof fetch = async (input, init) => {
      seen.push(new Request(input, init));
      return new Response("{}", { headers: { "content-type": "application/json" } });
    };
    const headerValue = "private-header-fixture";
    const apiKey = "fixture-api-key";
    const secretKey = "fixture-secret-key";
    const client = new FutureAGIClient({
      baseUrl: "http://127.0.0.1:9",
      apiKey,
      secretKey,
      extraHeaders: { "X-Private": headerValue },
      fetch: transport,
      retries: 0,
    });
    const copy = client.withOptions({ timeoutMs: 500 });
    for (const current of [client, copy]) {
      for (const text of [inspect(current, { depth: null }), JSON.stringify(current)]) {
        for (const value of [headerValue, apiKey, secretKey]) {
          expect(text).not.toContain(value);
        }
      }
      await current.generatedClient.get({ url: "/probe" });
    }
    expect(seen).toHaveLength(2);
    for (const request of seen) {
      expect(request.headers.get("x-private")).toBe(headerValue);
      expect(request.headers.get("x-api-key")).toBe(apiKey);
      expect(request.headers.get("x-secret-key")).toBe(secretKey);
    }
  } finally {
    if (saved === undefined) delete process.env.FI_EXTRA_HEADERS;
    else process.env.FI_EXTRA_HEADERS = saved;
  }
});
