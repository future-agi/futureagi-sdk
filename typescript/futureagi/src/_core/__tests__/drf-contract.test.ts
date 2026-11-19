import fs from "node:fs";
import path from "node:path";
import { FutureAGIClient } from "../../futureagi-client";
import { Resource, type CatalogOperation } from "../catalog";
import { pathArgs, type Case } from "../__fixtures__/contract-runtime";

class DRFResource extends Resource {
  invoke(op: CatalogOperation) { return this.call(op, pathArgs({ path_params: op.path_params }), {}, undefined); }
}

test("DRF pages preserve all six fields and never follow a foreign origin", async () => {
  const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/contracts/operations.json"), "utf8"));
  const row: Case = data.operations.find((r: Case) => r.adapter === "catalog" && r.method === "GET");
  const requests: Request[] = [];
  const fetcher = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init);
    requests.push(request);
    const page = Number(new URL(request.url).searchParams.get("page"));
    return Response.json({ status: true, result: {
      count: 2, next: page === 1 ? "http://foreign.invalid/ignored?page=2" : null,
      previous: page === 1 ? null : "?page=1", results: [{ page }], total_pages: 2, current_page: page,
    } });
  }) as typeof fetch;
  const client = new FutureAGIClient({ apiKey: "contract-api", secretKey: "contract-secret", baseUrl: "http://127.0.0.1:9", fetch: fetcher, retries: 0 });
  const op: CatalogOperation = { ...row.catalog, query: ["page", "page_size"], unwrap: "result",
    pagination: { page_param: "page", size_param: "page_size", first_page: 1, items: "results", next: "next", total_items: "count" } };
  const first = await new DRFResource(client.generatedClient).invoke(op);
  expect(first.items).toEqual([{ page: 1 }]);
  expect(first.hasMore).toBe(true);
  expect(first.raw).toEqual({ count: 2, next: "http://foreign.invalid/ignored?page=2", previous: null,
    results: [{ page: 1 }], total_pages: 2, current_page: 1 });
  const second = await first.nextPage();
  expect(second.raw).toEqual({ count: 2, next: null, previous: "?page=1", results: [{ page: 2 }], total_pages: 2, current_page: 2 });
  expect(second.hasMore).toBe(false);
  expect(await second.nextPage()).toBeUndefined();
  expect(requests).toHaveLength(2);
  expect(requests.every(r => new URL(r.url).hostname === "127.0.0.1")).toBe(true);
  expect(new URL(requests[0].url).pathname).toBe(new URL(requests[1].url).pathname);
});
