/**
 * Pages; the twin of Python's `fi._core.pagination`. A paginated `list()` returns a
 * {@link PagePromise}: awaiting it gives the first {@link Page}; `for await (const item of list())`
 * walks every item across pages, as in openai-node. `page.items`, `hasMore`, `nextCursor` and
 * `nextPage()` work page by page. Cursors are opaque; a cursor the server repeats ends the walk.
 */

import type { CallOptions, PlatformCore } from "./platform-base";
import type { PaginationSpec } from "./policy";
import type { OperationParams } from "./request";

export function dig(data: unknown, dotted: string | undefined): unknown {
  if (dotted === undefined) return undefined;
  let current = data;
  for (const part of dotted.split(".")) {
    if (current === null || typeof current !== "object" || Array.isArray(current)) return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

type Fetch = (cursor: string) => Promise<unknown>;

/** One page of a list. */
export class Page<T> implements AsyncIterable<T> {
  /** Transformed items in this page only. */
  readonly items: T[];
  /** Opaque cursor for the next page; absent when missing, empty or already seen. */
  readonly nextCursor?: string;
  /** Whether another page can be fetched without repeating a cursor. */
  readonly hasMore: boolean;
  /** Whether the server reports that this response was truncated. */
  readonly truncated: boolean;

  constructor(
    /** Unmodified response body for this page. */
    readonly raw: unknown,
    private readonly spec: PaginationSpec | undefined,
    private readonly fetchPage: Fetch,
    private readonly transform: ((item: unknown) => T) | undefined,
    private readonly seen: ReadonlySet<string> = new Set(),
  ) {
    const found = Array.isArray(raw) ? raw : dig(raw, spec?.itemsField);
    const values = Array.isArray(found) ? found : [];
    this.items = transform !== undefined ? values.map(transform) : (values as T[]);
    const cursor = spec?.style === "cursor" ? dig(raw, spec.nextCursorField) : undefined;
    if (typeof cursor === "string" && cursor !== "" && !seen.has(cursor)) this.nextCursor = cursor;
    const flag = spec?.hasMoreField !== undefined ? dig(raw, spec.hasMoreField) : undefined;
    this.hasMore = this.nextCursor !== undefined && flag !== false;
    this.truncated = spec?.truncatedField !== undefined ? Boolean(dig(raw, spec.truncatedField)) : false;
  }

  /** The next page, or undefined at the end. */
  async nextPage(): Promise<Page<T> | undefined> {
    if (!this.hasMore || this.nextCursor === undefined) return undefined;
    const seen = new Set([...this.seen, this.nextCursor]);
    return new Page(await this.fetchPage(this.nextCursor), this.spec, this.fetchPage, this.transform, seen);
  }

  /** Yield every item, fetching subsequent pages only as iteration advances. */
  async *[Symbol.asyncIterator](): AsyncIterator<T> {
    let page: Page<T> | undefined = this;
    while (page !== undefined) {
      for (const item of page.items) yield item;
      page = await page.nextPage();
    }
  }
}

/** `await list()` for the first page; `for await (const item of list())` for every item. */
export class PagePromise<T> implements PromiseLike<Page<T>>, AsyncIterable<T> {
  constructor(private readonly first: Promise<Page<T>>) {
    first.catch(() => undefined);
  }

  then<R1 = Page<T>, R2 = never>(
    onFulfilled?: ((value: Page<T>) => R1 | PromiseLike<R1>) | null,
    onRejected?: ((reason: unknown) => R2 | PromiseLike<R2>) | null,
  ): Promise<R1 | R2> {
    return this.first.then(onFulfilled, onRejected);
  }

  /** Yield every item, fetching subsequent pages only as iteration advances. */
  async *[Symbol.asyncIterator](): AsyncIterator<T> {
    yield* await this.first;
  }
}

/** A paginated operation's list: the first page (starting at `cursor`), lazily walked. */
export function listPage<T = unknown>(
  core: PlatformCore,
  name: string,
  params: OperationParams = {},
  options: CallOptions & { cursor?: string; transform?: (item: unknown) => T } = {},
): PagePromise<T> {
  const spec = core.operation(name).pagination;
  const { cursor, transform, ...callOptions } = options;
  const query = (next: string | undefined) => {
    if (next === undefined) return params.query ?? {};
    if (spec?.cursorParam === undefined) throw new TypeError(`${name} returns a single page; there is no cursor to pass`);
    return { ...(params.query ?? {}), [spec.cursorParam]: next };
  };
  const fetchPage: Fetch = (next) => Promise.resolve(core.call(name, { ...params, query: query(next) }, callOptions));
  const first = (async () =>
    new Page<T>(await core.call(name, { ...params, query: query(cursor) }, callOptions), spec, fetchPage, transform))();
  return new PagePromise(first);
}
