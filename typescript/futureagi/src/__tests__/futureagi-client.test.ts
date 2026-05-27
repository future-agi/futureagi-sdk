import { FutureAGIClient } from "../futureagi-client";

describe("FutureAGIClient", () => {
  it("sends auth headers and query params through the generated client", async () => {
    const fetchMock = jest.fn(async (request: Request) => {
      expect(request.headers.get("X-Api-Key")).toBe("api-key");
      expect(request.headers.get("X-Secret-Key")).toBe("secret-key");

      const url = new URL(request.url);
      expect(url.origin).toBe("http://api.test");
      expect(url.pathname).toBe("/model-hub/annotation-queues/");
      expect(url.searchParams.get("limit")).toBe("10");

      return new Response(JSON.stringify({ count: 0, results: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new FutureAGIClient({
      apiKey: "api-key",
      secretKey: "secret-key",
      baseUrl: "http://api.test",
      fetch: fetchMock as unknown as typeof fetch,
    });

    await expect(client.annotationQueues.list({ limit: 10 })).resolves.toEqual({
      count: 0,
      results: [],
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("wraps annotation discussion comments with clean method names", async () => {
    const fetchMock = jest.fn(async (request: Request) => {
      const url = new URL(request.url);
      expect(request.method).toBe("POST");
      expect(url.pathname).toBe(
        "/model-hub/annotation-queues/q1/items/i1/discussion/",
      );
      await expect(request.json()).resolves.toEqual({
        comment: "@reviewer please check this item",
        mentioned_user_ids: ["u1"],
      });

      return new Response(
        JSON.stringify({ status: true, result: { threads: [], comments: [] } }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });

    const client = new FutureAGIClient({
      apiKey: "api-key",
      secretKey: "secret-key",
      baseUrl: "http://api.test",
      fetch: fetchMock as unknown as typeof fetch,
    });

    await client.annotationQueues.discussion.comment("q1", "i1", {
      comment: "@reviewer please check this item",
      mentioned_user_ids: ["u1"],
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("wraps common dataset, experiment, simulation, tracing, user, and alert paths", async () => {
    const expected = [
      ["GET", "/model-hub/develops/dataset-1/get-dataset-table/"],
      ["GET", "/model-hub/experiments/v2/experiment-1/rows/"],
      ["GET", "/simulate/run-tests/run-test-1/status/"],
      ["GET", "/tracer/trace/list_voice_calls/"],
      ["GET", "/accounts/user-info/"],
      ["GET", "/tracer/user-alert-logs/alert-1/list/"],
    ];
    const fetchMock = jest.fn(async (request: Request) => {
      const [method, pathname] = expected.shift() ?? [];
      const url = new URL(request.url);
      expect(request.method).toBe(method);
      expect(url.pathname).toBe(pathname);
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new FutureAGIClient({
      apiKey: "api-key",
      secretKey: "secret-key",
      baseUrl: "http://api.test",
      fetch: fetchMock as unknown as typeof fetch,
    });

    await client.datasets.getTable("dataset-1", { limit: 5 });
    await client.experiments.rows("experiment-1", { page: 1 });
    await client.simulations.runTests.status("run-test-1");
    await client.tracing.voiceCalls({ project_id: "project-1" });
    await client.users.current();
    await client.alerts.logsForAlert("alert-1");

    expect(fetchMock).toHaveBeenCalledTimes(6);
    expect(expected).toHaveLength(0);
  });
});
