import { FutureAGIClient } from "../../futureagi-client";
import { Models } from "../../generated/catalog/models";
import type { CatalogOperation } from "../catalog";
import {
  AuthenticationError, ConfigurationError, PermissionDeniedError,
  ProductNotAvailableError, UnexpectedRedirectError,
} from "../errors";
import { CoreRateLimitError, CoreServerError } from "../__fixtures__/platform";

const path = "/model-hub/api/models_list/";
const options = {
  apiKey: "catalog-api", secretKey: "catalog-secret", baseUrl: "http://localhost:9031",
  workspaceId: "workspace-a", organizationId: "org-a", retries: 0,
};

function make(handler: (request: Request) => Response) {
  const seen: Request[] = [];
  const fakeFetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = input instanceof Request ? input : new Request(input, init);
    seen.push(request);
    return handler(request);
  };
  return { client: new FutureAGIClient({ ...options, fetch: fakeFetch as typeof fetch }), seen };
}

function response(value: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json", ...headers } });
}

test("platform model catalog uses shared credentials and declared filters", async () => {
  const row = { model_name: "example/model", is_available: false, new_field: 12 };
  const { client, seen } = make(request => {
    const url = new URL(request.url);
    expect(url.host).toBe("localhost:9031");
    expect(url.pathname).toBe(path);
    expect(request.method).toBe("GET");
    expect(request.headers.get("x-api-key")).toBe("catalog-api");
    expect(request.headers.get("x-secret-key")).toBe("catalog-secret");
    expect(request.headers.get("x-workspace-id")).toBe("workspace-a");
    expect(request.headers.get("x-organization-id")).toBe("org-a");
    expect(request.headers.has("authorization")).toBe(false);
    expect(request.headers.has("idempotency-key")).toBe(false);
    expect(url.searchParams.get("search")).toBe("example model");
    expect(url.searchParams.getAll("exclude_providers")).toEqual(["one", "two"]);
    return response({ count: 1, results: [row], next: null });
  });
  const page = await client.models.list({ search: "example model", limit: 10, model_type: "llm", exclude_providers: ["one", "two"] });
  expect(page.items).toEqual([row]);
  expect(page.hasMore).toBe(false);
  expect(seen).toHaveLength(1);
});

test("pagination retains filters and ignores a foreign next-link origin", async () => {
  const { client, seen } = make(request => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page"));
    expect(url.host).toBe("localhost:9031");
    expect(url.pathname).toBe(path);
    expect(url.searchParams.get("search")).toBe("example");
    expect(url.searchParams.get("limit")).toBe("100");
    return response({ count: 3, results: [{ id: page }],
      next: page < 3 ? `https://untrusted.invalid/other?page=${page + 1}` : null });
  });
  const rows = [];
  for await (const row of client.models.list({ search: "example", limit: 100 })) rows.push(row);
  expect(rows).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }]);
  expect(seen).toHaveLength(3);
});

test.each([
  [5, 3, [{ id: 5 }]], [6, 3, [{ id: 5 }, { id: 6 }]], [0, 1, []],
] as const)("last-page selection is terminal for %i records", async (count, current_page, results) => {
  const payload = { count, current_page, results, next: null };
  const { client, seen } = make(request => {
    expect(seen).toHaveLength(1);
    const query = new URL(request.url).searchParams;
    expect(query.get("page")).toBe("last");
    expect(query.get("limit")).toBe("100");
    expect(query.get("search")).toBe("example");
    return response(payload);
  });
  const page = await client.models.list({ page: "last", limit: 100, search: "example" });
  expect(page.raw).toEqual(payload);
  expect(page.hasMore).toBe(false);
  expect(await page.nextPage()).toBeUndefined();
  const items = [];
  for await (const item of page) items.push(item);
  expect(items).toEqual(results);
  expect(seen).toHaveLength(1);
});

test("catalog uses the resolved page for continuation", async () => {
  const { client, seen } = make(() => response({ count: 6, current_page: 3,
    results: [{ id: 5 }, { id: 6 }], next: null }));
  const page = await client.models.list({ page: 1, limit: 2 });
  expect(page.items).toEqual([{ id: 5 }, { id: 6 }]);
  expect(page.hasMore).toBe(false);
  expect(seen).toHaveLength(1);
});

test.each([
  [401, "unauthenticated", AuthenticationError],
  [403, "forbidden", PermissionDeniedError],
  [403, "product_not_admitted", PermissionDeniedError],
  [404, "product_not_admitted", ProductNotAvailableError],
  [429, "rate_limited", CoreRateLimitError],
  [500, "server_error", CoreServerError],
  [302, undefined, UnexpectedRedirectError],
] as const)("catalog error %s retains its shared class", async (status, code, error) => {
  const { client, seen } = make(() => response({ code }, status, {
    "x-request-id": "catalog-request", "retry-after": "2", location: "https://untrusted.invalid/credentials",
  }));
  await expect(client.models.list()).rejects.toBeInstanceOf(error);
  expect(seen).toHaveLength(1);
});

test("undeclared tenant filter is refused before fetch", async () => {
  const { client, seen } = make(() => { throw new Error("unexpected network request"); });
  await expect(client.models.list({ organization_id: "org-b" })).rejects.toBeInstanceOf(ConfigurationError);
  expect(seen).toHaveLength(0);
});

const declaredQuery = ["page", "limit", "name", "search", "model_type", "exclude_providers"];

// Change only the declaration at the real generated-method/catalog-adapter seam.
// The shared serializer and fetch transport still execute normally.
class DeclarationModels extends Models {
  constructor(client: FutureAGIClient["generatedClient"], private readonly declaration: string[]) {
    super(client);
  }
  protected override call(op: CatalogOperation, values: Record<string, string>, query: Record<string, unknown>, body: unknown) {
    return super.call({ ...op, query: [...this.declaration] }, values, query, body);
  }
}

test.each([
  ["source", declaredQuery], ["reversed", [...declaredQuery].reverse()], ["canonical", [...declaredQuery].sort()],
] as const)("wire query ignores %s declaration and caller order", async (_label, declaration) => {
  const { client, seen } = make(() => response({ count: 0, results: [], next: null }));
  const models = new DeclarationModels(client.generatedClient, [...declaration]);
  for (const values of [["z", "a"], ["a", "z"]]) {
    const pairs: [string, unknown][] = [["page", 2], ["limit", 3], ["name", "n"], ["search", "a b"],
      ["model_type", "llm"], ["exclude_providers", values]];
    const expected = `?exclude_providers=${values[0]}&exclude_providers=${values[1]}&limit=3&model_type=llm&name=n&page=2&search=a+b`;
    for (const caller of [pairs, [...pairs].reverse()]) {
      await models.list(Object.fromEntries(caller));
      expect(new URL(seen[seen.length - 1].url).search).toBe(expected);
    }
  }
  expect(seen).toHaveLength(4);
  await expect(models.list({ organization_id: "org-b" })).rejects.toBeInstanceOf(ConfigurationError);
  expect(seen).toHaveLength(4);
});

test("missing nonpaging declaration refuses filter before fetch", async () => {
  const { client, seen } = make(() => { throw new Error("unexpected network request"); });
  const models = new DeclarationModels(client.generatedClient, declaredQuery.filter(key => key !== "search"));
  await expect(models.list({ search: "a b" })).rejects.toBeInstanceOf(ConfigurationError);
  expect(seen).toHaveLength(0);
});

test("option copies preserve model namespace and selectors", async () => {
  const { client, seen } = make(() => response({ count: 0, results: [], next: null }));
  const clone = client.withOptions({ timeoutMs: 2000 });
  expect(clone.models).not.toBe(client.models);
  expect((await clone.models.list()).items).toEqual([]);
  expect(seen[0].headers.get("x-organization-id")).toBe("org-a");
});
