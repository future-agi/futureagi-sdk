import { AgentCC } from "../client";

function mockJsonResponse(data: Record<string, unknown>) {
  return jest.fn().mockResolvedValue(
    new Response(JSON.stringify(data), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  );
}

const batchObj = {
  id: "batch_abc",
  object: "batch",
  endpoint: "/v1/chat/completions",
  input_file_id: "file-abc",
  status: "completed",
  created_at: 1700000000,
};

describe("batches resource", () => {
  it("create() sends POST to /v1/batches", async () => {
    const mockFetch = mockJsonResponse(batchObj);
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.batches.create({
      input_file_id: "file-abc",
      endpoint: "/v1/chat/completions",
      completion_window: "24h",
    });

    expect(result.id).toBe("batch_abc");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.input_file_id).toBe("file-abc");
    expect(body.endpoint).toBe("/v1/chat/completions");
  });

  it("list() sends GET to /v1/batches", async () => {
    const mockFetch = mockJsonResponse({
      object: "list",
      data: [batchObj],
      has_more: false,
    });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.batches.list({ limit: 10 });

    expect(result.data).toHaveLength(1);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/batches");
    expect(url).toContain("limit=10");
  });

  it("retrieve() sends GET to /v1/batches/:id", async () => {
    const mockFetch = mockJsonResponse(batchObj);
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.batches.retrieve("batch_abc");

    expect(result.id).toBe("batch_abc");
    expect(mockFetch.mock.calls[0][0]).toContain("/v1/batches/batch_abc");
  });

  it("cancel() sends POST to /v1/batches/:id/cancel", async () => {
    const mockFetch = mockJsonResponse({ ...batchObj, status: "cancelling" });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.batches.cancel("batch_abc");

    expect(result.status).toBe("cancelling");
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/batches/batch_abc/cancel");
    expect(init.method).toBe("POST");
  });
});
