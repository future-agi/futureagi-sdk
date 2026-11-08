import { describe, it, expect } from "@jest/globals";
import { PaginatedList } from "../src/pagination.js";

describe("PaginatedList", () => {
  it("iterates through a single page", async () => {
    const page = new PaginatedList([1, 2, 3], false, null);
    const items: number[] = [];
    for await (const item of page) {
      items.push(item);
    }
    expect(items).toEqual([1, 2, 3]);
  });

  it("iterates through multiple pages", async () => {
    const page3 = new PaginatedList([7, 8, 9], false, null);
    const page2 = new PaginatedList([4, 5, 6], true, async () => page3);
    const page1 = new PaginatedList([1, 2, 3], true, async () => page2);

    const items: number[] = [];
    for await (const item of page1) {
      items.push(item);
    }
    expect(items).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
  });

  it("hasNextPage returns correct values", () => {
    const noNext = new PaginatedList([1], false, null);
    expect(noNext.hasNextPage()).toBe(false);

    const hasNext = new PaginatedList([1], true, async () => noNext);
    expect(hasNext.hasNextPage()).toBe(true);
  });

  it("getNextPage returns the next page", async () => {
    const page2 = new PaginatedList(["b"], false, null);
    const page1 = new PaginatedList(["a"], true, async () => page2);

    const next = await page1.getNextPage();
    expect(next.data).toEqual(["b"]);
    expect(next.hasNextPage()).toBe(false);
  });

  it("getNextPage throws when no more pages", async () => {
    const page = new PaginatedList([1], false, null);
    await expect(page.getNextPage()).rejects.toThrow("No next page");
  });

  it("handles empty pages", async () => {
    const page = new PaginatedList([], false, null);
    const items: unknown[] = [];
    for await (const item of page) {
      items.push(item);
    }
    expect(items).toEqual([]);
  });

  describe("fromDjango", () => {
    it("creates paginated list from Django format", async () => {
      const fetcher = async (url: string) => {
        expect(url).toBe("http://api/page2");
        return new PaginatedList([4, 5], false, null);
      };

      const page = PaginatedList.fromDjango(
        { results: [1, 2, 3], count: 5, next: "http://api/page2" },
        fetcher,
      );

      expect(page.data).toEqual([1, 2, 3]);
      expect(page.hasNextPage()).toBe(true);

      const items: number[] = [];
      for await (const item of page) {
        items.push(item);
      }
      expect(items).toEqual([1, 2, 3, 4, 5]);
    });

    it("no next page when next is null", () => {
      const page = PaginatedList.fromDjango(
        { results: [1], count: 1, next: null },
        async () => new PaginatedList([], false, null),
      );
      expect(page.hasNextPage()).toBe(false);
    });
  });

  describe("fromOpenAI", () => {
    it("creates paginated list from OpenAI format", async () => {
      const fetcher = async (afterId: string) => {
        expect(afterId).toBe("id-3");
        return new PaginatedList(
          [{ id: "id-4" }, { id: "id-5" }],
          false,
          null,
        );
      };

      const page = PaginatedList.fromOpenAI(
        { data: [{ id: "id-1" }, { id: "id-2" }, { id: "id-3" }], has_more: true, last_id: "id-3" },
        fetcher,
      );

      expect(page.data).toHaveLength(3);
      expect(page.hasNextPage()).toBe(true);

      const items: Array<{ id: string }> = [];
      for await (const item of page) {
        items.push(item);
      }
      expect(items).toHaveLength(5);
    });

    it("no next page when has_more is false", () => {
      const page = PaginatedList.fromOpenAI(
        { data: [{ id: "1" }], has_more: false },
        async () => new PaginatedList([], false, null),
      );
      expect(page.hasNextPage()).toBe(false);
    });
  });
});
