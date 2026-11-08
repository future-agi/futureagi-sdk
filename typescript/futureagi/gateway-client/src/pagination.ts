// ---------------------------------------------------------------------------
// PaginatedList — Auto-paginating async iterable for list endpoints
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors.js";

export class PaginatedList<T> {
  readonly data: T[];
  private _hasMore: boolean;
  private _fetchNext: (() => Promise<PaginatedList<T>>) | null;

  constructor(
    data: T[],
    hasMore: boolean,
    fetchNext: (() => Promise<PaginatedList<T>>) | null,
  ) {
    this.data = data;
    this._hasMore = hasMore;
    this._fetchNext = fetchNext;
  }

  hasNextPage(): boolean {
    return this._hasMore && this._fetchNext !== null;
  }

  async getNextPage(): Promise<PaginatedList<T>> {
    if (!this.hasNextPage()) {
      throw new AgentCCError("No next page available");
    }
    return this._fetchNext!();
  }

  async *[Symbol.asyncIterator](): AsyncGenerator<T> {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    let page: PaginatedList<T> = this;
    while (true) {
      for (const item of page.data) {
        yield item;
      }
      if (!page.hasNextPage()) break;
      page = await page.getNextPage();
    }
  }

  // -----------------------------------------------------------------------
  // Factory: Django REST Framework pagination format
  // { results: T[], count: number, next: string | null, previous: string | null }
  // -----------------------------------------------------------------------

  static fromDjango<T>(
    response: {
      results: T[];
      count: number;
      next: string | null;
    },
    fetcher: (url: string) => Promise<PaginatedList<T>>,
  ): PaginatedList<T> {
    return new PaginatedList<T>(
      response.results,
      response.next !== null,
      response.next ? () => fetcher(response.next!) : null,
    );
  }

  // -----------------------------------------------------------------------
  // Factory: OpenAI pagination format
  // { data: T[], has_more: boolean, first_id?: string, last_id?: string }
  // -----------------------------------------------------------------------

  static fromOpenAI<T>(
    response: {
      data: T[];
      has_more: boolean;
      last_id?: string;
    },
    fetcher: (afterId: string) => Promise<PaginatedList<T>>,
  ): PaginatedList<T> {
    return new PaginatedList<T>(
      response.data,
      response.has_more,
      response.has_more && response.last_id
        ? () => fetcher(response.last_id!)
        : null,
    );
  }
}
