/** FA catalog namespaces share the root's authenticated transport and typed errors. */
import type { Client } from "../generated/openapi/client";
import { Page, dig } from "./pagination";
import { BadRequestError, FutureAGIAPIError, NotFoundError } from "./errors";
import { buildBody, buildPath, buildQuery, type OperationParams } from "./request";
import type { HttpMethod, OperationSpec } from "./policy";

export interface CatalogOperation {
  id: string;
  public: string;
  method: string;
  path: string;
  path_params: string[];
  query: string[];
  operation_id: string | null;
  unwrap: string | null;
  pagination: null | {
    page_param: string;
    size_param: string;
    first_page: number;
    items: string;
    next?: string;
    total_items?: string;
    current_page?: string;
  };
}

function pageData(raw: unknown, spec: NonNullable<CatalogOperation["pagination"]>, query: Record<string, unknown>, pageSize?: number) {
  const found = dig(raw, spec.items);
  if (!Array.isArray(found)) throw new FutureAGIAPIError(200, undefined, {
    code: "invalid_page", message: "The response is missing its declared page items",
  });
  const items = found;
  const requested = query[spec.page_param] ?? spec.first_page;
  // DRF resolves "last" server-side. Do not infer a phantom next page from the
  // count and a short final page, whose length cannot reveal the page size.
  if (requested === "last") return { items, next: undefined, response: raw, guess: false };
  const resolved = dig(raw, spec.current_page);
  const current = typeof resolved === "number" && Number.isInteger(resolved) && resolved >= spec.first_page
    ? resolved : Number(requested);
  let next: string | undefined;
  const link = dig(raw, spec.next);
  if (typeof link === "string" && link) {
    // Only extract a page number; never follow a server-supplied host or path.
    try {
      const value = new URL(link, "http://localhost").searchParams.get(spec.page_param);
      const candidate = value === null ? NaN : Number(value);
      if (Number.isInteger(candidate) && candidate > current) next = String(candidate);
    } catch { /* A malformed next link ends the walk. */ }
  }
  const total = dig(raw, spec.total_items);
  // Learn the server cap even when the first request resumes after page one.
  // Subsequent short pages retain this effective size when counting prior rows.
  const size = pageSize ?? items.length;
  let guess = false;
  if (typeof total === "number" && items.length > 0 && size > 0 &&
      (current - spec.first_page) * size + items.length < total) {
    next = String(current + 1);
    // A resumed first page shorter than the size asked for is either the last page
    // or a server-capped one; only the next page can tell.
    const asked = Number(query[spec.size_param]);
    guess = pageSize === undefined && current > spec.first_page && (Number.isNaN(asked) || items.length < asked);
  }
  return { items, next: items.length ? next : undefined, response: raw, guess };
}

// FA's dataset optimization list answers a page past the end with 400 (its list view turns
// the paginator's not-found into a bad request); a plain paginated view answers 404.
const pastEnd = (error: unknown) => error instanceof BadRequestError || error instanceof NotFoundError;

class CatalogPage extends Page<unknown> {
  readonly raw: unknown;
  constructor(value: ReturnType<typeof pageData>, private readonly load: (cursor: string) => Promise<ReturnType<typeof pageData>>,
    private readonly visited: ReadonlySet<string> = new Set()) {
    super(value, { style: "cursor", itemsField: "items", cursorParam: "page", nextCursorField: "next" }, load, undefined, visited);
    this.raw = value.response;
  }
  async nextPage(): Promise<CatalogPage | undefined> {
    if (!this.hasMore || this.nextCursor === undefined) return undefined;
    return new CatalogPage(await this.load(this.nextCursor), this.load, new Set([...this.visited, this.nextCursor]));
  }
}

export class Resource {
  constructor(protected readonly client: Client, protected readonly headers: () => Record<string, string> = () => ({})) {}

  protected async call(op: CatalogOperation, path: Record<string, string>, query: Record<string, unknown>, body: unknown): Promise<any> {
    const spec: OperationSpec = {
      name: op.public, family: op.id.split(".")[0], method: op.method as HttpMethod,
      path: op.path, pathParams: op.path_params, query: op.query,
      body: ["POST", "PUT", "PATCH"].includes(op.method) ? "json" : "none",
    };
    const encoded = buildBody(spec, body);
    const request = async (q: Record<string, unknown>) => {
      const wire = { ...q };
      if (op.pagination) wire[op.pagination.page_param] ??= op.pagination.first_page;
      // Let FA validate free-form paging keys unchanged, including page bases.
      // Keep the existing fail-closed policy for other undeclared query keys.
      const paging = new Set(["page", "limit", "page_size", "page_number", "offset", "cursor", "cursor_mode", "current_page_index", "page_token"]);
      const wireSpec = { ...spec, query: [...new Set([...op.query, ...Object.keys(wire).filter(key => paging.has(key))])] };
      const value = await this.client.request({
        method: spec.method,
        url: buildPath(spec, path) + buildQuery(wireSpec, wire as OperationParams["query"]),
        body,
        headers: { ...this.headers(), ...(encoded.contentType ? { "Content-Type": encoded.contentType } : {}) },
        responseStyle: "data", throwOnError: true,
      });
      if (op.unwrap && value !== null && typeof value === "object" && op.unwrap in value) {
        return (value as Record<string, unknown>)[op.unwrap];
      }
      return value;
    };
    const raw = await request(query);
    const pagination = op.pagination;
    if (!pagination) return raw;
    const first = pageData(raw, pagination, query);
    const probe = first.guess ? first.next : undefined;
    // Keep the requested limit stable: resuming on a short final page cannot
    // reveal the cap, and changing the wire limit would change row offsets.
    const fetch = async (cursor: string): Promise<ReturnType<typeof pageData>> => {
      const q = { ...query, [pagination.page_param]: Number(cursor) };
      try {
        return pageData(await request(q), pagination, q, first.items.length);
      } catch (error) {
        if (cursor !== probe || !pastEnd(error)) throw error;
        return { items: [], next: undefined, response: undefined, guess: false };
      }
    };
    return new CatalogPage(first, fetch);
  }
}
