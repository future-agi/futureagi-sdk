import fs from "node:fs";
import path from "node:path";
import { runtime, pathArgs, type Case } from "../__fixtures__/contract-runtime";

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/contracts/operations.json"), "utf8"));
const rows: Case[] = data.operations.filter((row: Case) => row.adapter === "catalog" && row.catalog.pagination && data.public_cases.ts.includes(row.id));

function put(target: any, name: string, value: any): void {
  const parts = name.split(".");
  for (const key of parts.slice(0, -1)) target = target[key] ??= {};
  target[parts[parts.length - 1]] = value;
}

async function checkPages(row: Case, mutation?: string) {
  const descriptor = row.catalog;
  const page = descriptor.pagination;
  const requests: Request[] = [];
  const subject = runtime(row, request => {
    requests.push(request);
    const number = Number(new URL(request.url).searchParams.get(page.page_param));
    const raw = { count: 2, previous: null, total_pages: 2, current_page: number };
    put(raw, page.items, [{ n: number }]);
    if (page.total_items) put(raw, page.total_items, 2);
    if (page.next) put(raw, page.next, number === 1 ? "http://127.0.0.1:9/ignored?page=2" : null);
    return Response.json(descriptor.unwrap ? { [descriptor.unwrap]: raw } : raw);
  });
  const first = await subject.call();
  // Preserve raw while breaking the public Page. Both mutations must fail this gate.
  if (mutation) Object.defineProperty(first, mutation === "items" ? "items" : "hasMore", { value: mutation === "items" ? [] : false });
  expect(first.items).toEqual([{ n: 1 }]);
  expect(first.hasMore).toBe(true);
  expect(first.nextCursor).toBe("2");
  const second = await first.nextPage();
  expect(second.items).toEqual([{ n: 2 }]);
  expect(second.hasMore).toBe(false);
  expect(second.nextCursor == null).toBe(true);
  expect(await second.nextPage()).toBeUndefined();
  expect(requests).toHaveLength(2);
  expect(requests.map(r => r.method)).toEqual([row.method, row.method]);
  const urls = requests.map(r => new URL(r.url));
  let expectedPath = row.path;
  for (const [key, value] of Object.entries(pathArgs(row))) expectedPath = expectedPath.replace(`{${key}}`, value);
  expect(urls[0].pathname).toBe(expectedPath);
  expect(urls[1].pathname).toBe(expectedPath);
  expect(urls[1].searchParams.get(page.page_param)).toBe("2");
  urls.forEach(url => url.searchParams.delete(page.page_param));
  expect(urls[1].search).toBe(urls[0].search);
}

describe.each(rows)("public pagination $id", row => {
  test("walks two pages through the public operation", async () => checkPages(row));
  test.each(["items", "continuation"])("rejects broken %s with intact raw", async mutation => {
    await expect(checkPages(row, mutation)).rejects.toThrow();
  });
});
