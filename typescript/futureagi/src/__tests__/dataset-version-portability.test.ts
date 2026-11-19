import {
  decodeVersionJsonl,
  encodeVersionJsonl,
} from "../datasets/version-jsonl";
import { FutureAGIClient } from "../futureagi-client";
import type { DatasetVersionItemRead } from "../generated/openapi/types.gen";
import { readFileSync } from "node:fs";
import path from "node:path";

const datasetId = "11111111-1111-4111-8111-111111111111";
const version = {
  id: "22222222-2222-4222-8222-222222222222",
  dataset: datasetId,
  parent_version: null,
  description: "portable",
  metadata: { nullable: null, source: "fixture" },
  source_revision: "git:abc",
  content_hash: "a".repeat(64),
  item_count: 2,
};
const items: DatasetVersionItemRead[] = [
  {
    example_id: "44444444-4444-4444-8444-444444444444",
    external_id: "case-2",
    input: ["text", null],
    expected: null,
    metadata: { nested: null },
    source_trace_id: "trace",
    source_span_id: "span",
    content_hash: "b".repeat(64),
    legacy_row: null,
  },
  {
    example_id: "33333333-3333-4333-8333-333333333333",
    external_id: "case-1",
    input: { answer: false },
    expected: 0,
    metadata: { split: "eval" },
    source_trace_id: "",
    source_span_id: "",
    content_hash: "c".repeat(64),
    legacy_row: null,
  },
];

test("JSONL export is deterministic and round-trips complete cases", async () => {
  const first = await encodeVersionJsonl(version, items);
  const second = await encodeVersionJsonl(version, [...items].reverse());
  expect(first).toBe(second);
  const decoded = await decodeVersionJsonl(first, datasetId);
  expect(decoded.items).toHaveLength(2);
  expect(decoded.items[1].expected).toBeNull();
  expect(decoded.items[1].metadata).toEqual({ nested: null });
});

test("Python and TypeScript share the same archive for the documented fixture", async () => {
  const fixture = readFileSync(
    path.resolve(
      __dirname,
      "../../../../tests/fixtures/dataset-experiments/version-portability.jsonl",
    ),
    "utf8",
  );
  expect(await encodeVersionJsonl(version, items)).toBe(fixture);
  const decoded = await decodeVersionJsonl(
    new TextEncoder().encode(fixture),
    datasetId,
    { parentVersionId: version.id },
  );
  expect(decoded.parent_version_id).toBe(version.id);
  expect(decoded.description).toBe(version.description);
  expect(decoded.metadata).toEqual(version.metadata);
  expect(decoded.items[1].source_trace_id).toBe("trace");
});

test.each([false, true])(
  "export follows pages and handles late failure %s",
  async (lateFailure) => {
    let calls = 0;
    const fetch = jest.fn(async (request: Request) => {
      const index = calls++;
      expect(request.method).toBe("GET");
      expect(new URL(request.url).searchParams.get("offset")).toBe(
        String(index),
      );
      if (lateFailure && index === 1)
        return new Response(
          JSON.stringify({ status: false, detail: "hidden" }),
          { status: 403, headers: { "Content-Type": "application/json" } },
        );
      return new Response(
        JSON.stringify({
          status: true,
          result: {
            version,
            items: [items[index]],
            limit: 500,
            offset: index,
            has_more: index === 0,
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    const client = new FutureAGIClient({
      apiKey: "test",
      secretKey: "test",
      baseUrl: "http://api.test",
      fetch: fetch as unknown as typeof globalThis.fetch,
    });
    if (lateFailure)
      await expect(
        client.datasets.versions.exportJsonl(datasetId, version.id),
      ).rejects.toBeDefined();
    else
      expect(
        await client.datasets.versions.exportJsonl(datasetId, version.id),
      ).toBe(await encodeVersionJsonl(version, items));
    expect(calls).toBe(2);
  },
);

test("invalid lines never POST and an ambiguous write is not retried", async () => {
  const fetch = jest.fn(async () => {
    throw new Error("response lost");
  });
  const client = new FutureAGIClient({
    apiKey: "test",
    secretKey: "test",
    baseUrl: "http://api.test",
    fetch: fetch as unknown as typeof globalThis.fetch,
  });
  await expect(
    client.datasets.versions.importJsonl(datasetId, "invalid\n"),
  ).rejects.toThrow("JSONL");
  expect(fetch).not.toHaveBeenCalled();
  await expect(
    client.datasets.versions.importJsonl(
      datasetId,
      await encodeVersionJsonl(version, items),
    ),
  ).rejects.toThrow("response lost");
  expect(fetch).toHaveBeenCalledTimes(1);
});

test.each([
  { input: null },
  { metadata: [] },
  { example_id: "invalid" },
  { source_trace_id: null },
  { external_id: 123 },
  { legacy_row: "invalid" },
  { expected: NaN },
  { input: Number.MAX_SAFE_INTEGER + 1 },
])("rejects invalid case payloads before export", async (change) => {
  await expect(
    encodeVersionJsonl(version, [
      { ...items[0], ...change },
      items[1],
    ] as DatasetVersionItemRead[]),
  ).rejects.toThrow("JSONL");
});

test("requires exact declared count and rejects excessive UTF-8 bytes", async () => {
  await expect(
    encodeVersionJsonl({ ...version, item_count: 3 }, items),
  ).rejects.toThrow("item_count");
  await expect(
    decodeVersionJsonl(new Uint8Array(10 * 1024 * 1024 + 1), datasetId),
  ).rejects.toThrow("bytes");
  await expect(
    decodeVersionJsonl(new Uint8Array([255]), datasetId),
  ).rejects.toThrow("UTF-8");
});

test.each([
  [
    "format_version",
    (value: string) =>
      value.replace('"format_version":1', '"format_version":2'),
  ],
  [
    "checksum",
    (value: string) =>
      value.replace(
        /"records_sha256":"[0-9a-f]+"/,
        `"records_sha256":"${"0".repeat(64)}"`,
      ),
  ],
])("rejects invalid %s before creating a request", async (_name, mutate) => {
  const archive = await encodeVersionJsonl(version, items);
  await expect(decodeVersionJsonl(mutate(archive), datasetId)).rejects.toThrow(
    "JSONL line 1",
  );
});

test("legacy references require explicit same-dataset preservation or drop", async () => {
  const archive = await encodeVersionJsonl(version, [
    { ...items[0], legacy_row: "55555555-5555-4555-8555-555555555555" },
    items[1],
  ]);
  await expect(
    decodeVersionJsonl(archive, "66666666-6666-4666-8666-666666666666"),
  ).rejects.toThrow("legacy_row");
  const dropped = await decodeVersionJsonl(
    archive,
    "66666666-6666-4666-8666-666666666666",
    { legacyRows: "drop" },
  );
  expect(dropped.items.every((item) => item.legacy_row_id === undefined)).toBe(
    true,
  );
  const preserved = await decodeVersionJsonl(archive, datasetId, {
    legacyRows: "preserve",
  });
  expect(preserved.items[1].legacy_row_id).toBe(
    "55555555-5555-4555-8555-555555555555",
  );
});
