import { Client } from "../client";
import type { DatasetsCellsUpdateParams } from "../resources/base";
import type { FetchLike, RequestOptions } from "../transport";

const baseUrl = "https://sdk.invalid";
const datasetId = "dataset-1";
const cell = { row_id: "row-1", column_id: "column-1" };

function fixture() {
  const calls: Array<[string, RequestInit]> = [];
  const fetch: FetchLike = async (url, init) => {
    calls.push([url, init]);
    return new Response(
      JSON.stringify({ status: true, result: "Cell value updated successfully" }),
      { status: 200 },
    );
  };
  const client = new Client({ apiKey: "k", secretKey: "s", baseUrl, fetch });
  return { client, calls };
}

describe("dataset cell replacement values", () => {
  const missing: Array<[string, unknown, RequestOptions | undefined]> = [
    ["omitted", { ...cell }, undefined],
    ["undefined", { ...cell, new_value: undefined }, undefined],
    [
      "undefined body override",
      { ...cell, new_value: "replacement" },
      { extraBody: { new_value: undefined } },
    ],
  ];

  test.each(missing)("rejects %s new_value before any HTTP request", async (_label, params, options) => {
    const { client, calls } = fixture();
    // Model JavaScript/untyped callers without making RED fail on a TypeScript diagnostic.
    await expect(
      Promise.resolve().then(() => client.datasets.cells.update(datasetId, params as DatasetsCellsUpdateParams, options)),
    ).rejects.toThrow(/new_value.*required/);
    expect(calls).toHaveLength(0);
  });

  test.each(["replacement", "", null])("sends an explicit new_value of %p", async (new_value) => {
    const { client, calls } = fixture();
    await client.datasets.cells.update(datasetId, { ...cell, new_value });
    expect(calls).toHaveLength(1);
    const [url, init] = calls[0];
    expect(url).toBe(`${baseUrl}/model-hub/develops/${datasetId}/update_cell_value/`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ ...cell, new_value });
  });

  test.each(["override", "", null])("sends a deliberate body override of %p", async (new_value) => {
    const { client, calls } = fixture();
    const options: RequestOptions = {
      extraBody: { new_value, note: "kept" },
      extraQuery: { source: "test" },
      headers: { "X-Cell-Test": "kept" },
      maxRetries: 0,
    };
    await client.datasets.cells.update(datasetId, { ...cell, new_value: "replacement" }, options);
    expect(calls).toHaveLength(1);
    const [url, init] = calls[0];
    expect(url).toBe(`${baseUrl}/model-hub/develops/${datasetId}/update_cell_value/?source=test`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ ...cell, new_value, note: "kept" });
    expect(new Headers(init.headers).get("X-Cell-Test")).toBe("kept");
    expect(options.extraBody).toEqual({ new_value, note: "kept" });
  });

  test("dispatches the validated body snapshot without re-reading overrides", async () => {
    const { client, calls } = fixture();
    let reads = 0;
    const extraBody = {
      get new_value(): string | undefined {
        reads += 1;
        return reads === 1 ? "replacement" : undefined;
      },
    };
    await client.datasets.cells.update(datasetId, { ...cell, new_value: "original" }, { extraBody });
    expect(reads).toBe(1);
    expect(calls).toHaveLength(1);
    expect(JSON.parse(calls[0][1].body as string)).toEqual({ ...cell, new_value: "replacement" });
  });
});
