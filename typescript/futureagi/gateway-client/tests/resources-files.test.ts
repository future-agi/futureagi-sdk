import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

function mockJsonResponse(data: Record<string, unknown>) {
  return jest.fn<any>().mockResolvedValue(
    new Response(JSON.stringify(data), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  );
}

const fileObj = {
  id: "file-abc",
  object: "file",
  bytes: 1234,
  created_at: 1700000000,
  filename: "data.jsonl",
  purpose: "batch",
};

describe("files resource", () => {
  it("create() sends POST with FormData to /v1/files", async () => {
    const mockFetch = mockJsonResponse(fileObj);
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const blob = new Blob(["test content"], { type: "application/jsonl" });
    const result = await client.files.create({
      file: blob,
      purpose: "batch",
    });

    expect(result.id).toBe("file-abc");
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/files");
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
  });

  it("list() sends GET to /v1/files", async () => {
    const mockFetch = mockJsonResponse({ data: [fileObj], object: "list" });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.files.list();

    expect(result.data).toHaveLength(1);
    expect(mockFetch.mock.calls[0][1].method).toBe("GET");
  });

  it("retrieve() sends GET to /v1/files/:id", async () => {
    const mockFetch = mockJsonResponse(fileObj);
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.files.retrieve("file-abc");

    expect(result.id).toBe("file-abc");
    expect(mockFetch.mock.calls[0][0]).toContain("/v1/files/file-abc");
  });

  it("content() sends GET to /v1/files/:id/content", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response("file content bytes", { status: 200 }),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.files.content("file-abc");

    expect(result).toBeInstanceOf(Response);
    expect(mockFetch.mock.calls[0][0]).toContain("/v1/files/file-abc/content");
  });

  it("delete() sends DELETE to /v1/files/:id", async () => {
    const mockFetch = mockJsonResponse({ id: "file-abc", deleted: true });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.files.delete("file-abc");

    expect(result.deleted).toBe(true);
    expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
  });
});
