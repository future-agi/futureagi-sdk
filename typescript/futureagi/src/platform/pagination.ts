// Auto-pagination over the backend's several page styles; see the Python `_pagination.py`.

export interface Pagination {
  page_param: string;
  size_param: string;
  first_page: number;
  items: string;
  next?: string;
  total_pages?: string;
  total_items?: string;
}

export interface Page<T> {
  items: T[];
  number: number;
  raw: unknown;
}

const MAX_PAGES = 10_000; // guard against a server that never says "last page"

export function getPath(data: unknown, dotted: string): unknown {
  let current: unknown = data;
  for (const part of dotted.split(".")) {
    if (typeof current !== "object" || current === null || Array.isArray(current)) {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

/** `for await (const item of client.datasets.list())` walks every page; `firstPage()` fetches one. */
export class Pager<T> implements AsyncIterable<T> {
  constructor(
    private readonly fetch: (page: number) => Promise<unknown>,
    private readonly spec: Pagination,
  ) {}

  async firstPage(): Promise<Page<T>> {
    const page = this.spec.first_page;
    const raw = await this.fetch(page);
    return { items: this.items(raw), number: page, raw };
  }

  async *[Symbol.asyncIterator](): AsyncIterator<T> {
    let page = this.spec.first_page;
    let seen = 0;
    for (let i = 0; i < MAX_PAGES; i++) {
      const raw = await this.fetch(page);
      const items = this.items(raw);
      seen += items.length;
      yield* items;
      if (this.isLast(raw, page, items.length, seen)) {
        return;
      }
      page += 1;
    }
  }

  async toArray(limit?: number): Promise<T[]> {
    const out: T[] = [];
    for await (const item of this) {
      out.push(item);
      if (limit !== undefined && out.length >= limit) {
        break;
      }
    }
    return out;
  }

  private items(raw: unknown): T[] {
    const items = getPath(raw, this.spec.items);
    return Array.isArray(items) ? (items as T[]) : [];
  }

  private isLast(raw: unknown, page: number, count: number, seen: number): boolean {
    if (count === 0) {
      return true;
    }
    if (this.spec.next !== undefined) {
      return !getPath(raw, this.spec.next);
    }
    if (this.spec.total_items !== undefined) {
      const total = getPath(raw, this.spec.total_items);
      return typeof total !== "number" || seen >= total;
    }
    const total = getPath(raw, this.spec.total_pages as string);
    return typeof total !== "number" || page - this.spec.first_page + 1 >= total;
  }
}
