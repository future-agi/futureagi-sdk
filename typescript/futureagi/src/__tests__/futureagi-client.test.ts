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

  it("wraps eval and simulation eval configuration paths", async () => {
    const expected = [
      ["POST", "/model-hub/eval-templates/list/"],
      ["POST", "/model-hub/eval-templates/create-v2/"],
      ["GET", "/model-hub/eval-templates/eval-template-1/detail/"],
      ["PUT", "/model-hub/eval-templates/eval-template-1/update/"],
      ["GET", "/model-hub/eval-templates/eval-template-1/versions/"],
      ["POST", "/sdk/api/v1/new-eval/"],
      ["GET", "/sdk/api/v1/new-eval/"],
      ["POST", "/simulate/run-tests/run-test-1/eval-configs/"],
      [
        "GET",
        "/simulate/run-tests/run-test-1/eval-configs/eval-config-1/get-structure/",
      ],
      ["GET", "/simulate/run-tests/run-test-1/eval-summary/"],
      ["POST", "/simulate/run-tests/run-test-1/run-new-evals/"],
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

    await client.evals.listTemplates({ filters: {} } as any);
    await client.evals.createTemplate({ name: "Faithfulness" } as any);
    await client.evals.getTemplate("eval-template-1");
    await client.evals.updateTemplate("eval-template-1", {
      name: "Faithfulness v2",
    } as any);
    await client.evals.templateVersions("eval-template-1");
    await client.evals.runV2({ eval_id: "run-1", data: [] } as any);
    await client.evals.getRunV2("11111111-1111-1111-1111-111111111111");
    await client.simulations.runTests.addEvalConfigs("run-test-1", {
      eval_configs: [{ eval_id: "eval-template-1" }],
    } as any);
    await client.simulations.runTests.evalConfigStructure(
      "run-test-1",
      "eval-config-1",
    );
    await client.simulations.runTests.evalSummary("run-test-1", {
      test_execution_id: "te-1",
    });
    await client.simulations.runTests.runNewEvals("run-test-1", {
      test_execution_ids: ["te-1"],
      eval_config_ids: ["cfg-1"],
    } as any);

    expect(fetchMock).toHaveBeenCalledTimes(11);
    expect(expected).toHaveLength(0);
  });
});
