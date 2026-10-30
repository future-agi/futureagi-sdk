// What the catalog guarantees about the generated client, and how it is extended (no backend).

import { Client } from "../client";
import { OP_DATASETS_ROWS_ADD } from "../_operations";
import { DatasetsColumnsResource, DatasetsResource } from "../resources/base";
import { Datasets } from "../resources/datasets";
import { resetStabilityWarnings } from "../stability";
import type { FetchLike, Transport } from "../transport";

const ok: FetchLike = async () => new Response(JSON.stringify({ status: true, result: { ids: ["s1"] } }), { status: 200 });

describe("configuration", () => {
  const env = { ...process.env };
  afterEach(() => {
    process.env = { ...env };
  });

  test("reads keys and the base URL from the environment", async () => {
    process.env.FI_API_KEY = "env-key";
    process.env.FI_SECRET_KEY = "env-secret";
    process.env.FI_BASE_URL = "http://env.test/";
    const calls: Array<[string, RequestInit]> = [];
    const client = new Client({ fetch: async (url, init) => (calls.push([url, init]), ok(url, init)) });
    await client.request("GET", "/x/");
    expect(calls[0][0]).toBe("http://env.test/x/");
    expect(calls[0][1].headers).toMatchObject({ "X-Api-Key": "env-key", "X-Secret-Key": "env-secret" });
  });

  test("fails fast without keys", () => {
    delete process.env.FI_API_KEY;
    delete process.env.FI_SECRET_KEY;
    expect(() => new Client({ fetch: ok })).toThrow(/FI_API_KEY/);
    expect(() => new Client({ apiKey: "k", secretKey: "s", fetch: ok, maxRetries: -1 })).toThrow(/maxRetries/);
  });
});

describe("resources", () => {
  const client = () => new Client({ apiKey: "k", secretKey: "s", baseUrl: "http://unused", fetch: ok });

  test("every top-level resource and nested resource is wired, with camelCase names", () => {
    const c = client();
    expect(c.datasets).toBeInstanceOf(Datasets);
    expect(c.datasets.columns).toBeInstanceOf(DatasetsColumnsResource);
    expect("createFromFile" in c.knowledgeBases).toBe(false); // that one is on datasets
    expect(typeof c.datasets.createFromFile).toBe("function");
    expect(typeof c.annotationQueues.items.importAnnotations).toBe("function");
    expect(typeof c.spans.ingest).toBe("function"); // hand-written in resources/spans.ts
  });

  test("resource classes can be swapped, nested ones too, and new ones added", async () => {
    class Columns extends DatasetsColumnsResource {
      mine(): string {
        return "custom columns";
      }
    }
    class MyDatasets extends Datasets {
      declare columns: Columns;
      constructor(transport: Transport) {
        super(transport);
        this.columns = new Columns(transport);
      }
      mine(): string {
        return "custom datasets";
      }
    }
    const c = new Client({ apiKey: "k", secretKey: "s", baseUrl: "http://unused", fetch: ok, resources: { datasets: MyDatasets } });
    const datasets = c.datasets as MyDatasets;
    expect(datasets.mine()).toBe("custom datasets");
    expect(datasets.columns.mine()).toBe("custom columns");
    expect(typeof datasets.columns.add).toBe("function"); // generated methods still there
    expect(datasets).toBeInstanceOf(DatasetsResource);

    class Billing {
      constructor(readonly transport: Transport) {}
      invoices(): Promise<unknown> {
        return this.transport.raw("GET", "/billing/invoices/");
      }
    }
    class MyClient extends Client {
      readonly billing = new Billing(this.transport);
    }
    expect(await new MyClient({ apiKey: "k", secretKey: "s", baseUrl: "http://unused", fetch: ok }).billing.invoices()).toEqual({ ids: ["s1"] });
  });

  test("beta methods warn once", async () => {
    resetStabilityWarnings();
    const warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    try {
      expect(OP_DATASETS_ROWS_ADD.id).toBe("datasets.rows.add");
      const c = client();
      await c.datasets.rows.add("d1", { rows: [] });
      await c.datasets.rows.add("d1", { rows: [] });
      expect(warn).toHaveBeenCalledTimes(1);
      expect(warn.mock.calls[0][0]).toContain("datasets.rows.add is in beta");
    } finally {
      warn.mockRestore();
    }
  });
});
