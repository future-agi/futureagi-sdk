import { spawnSync } from "node:child_process";
import { resolve } from "node:path";

// Run the actual test:live entry point against the real SDK, but replace every
// transport with local fixtures. tsx deliberately matches the operator command's
// transpile-only behavior; the package typecheck does not include tests/live/.
const fixture = `
  const assert = require("node:assert/strict");
  const origin = "http://sdk-smoke.invalid";
  const responses = new Map([
    ["/accounts/user-info/", { result: { id: "fixture-user" } }],
    ["/accounts/workspace/list/", { result: { workspaces: [{}] } }],
    ["/model-hub/develops/get-datasets-names/", { result: { datasets: [{}] } }],
    ["/sdk/api/v1/get-evals/", { result: [] }],
    ["/tracer/project/list_projects/", { result: { projects: [{}] } }],
    ["/tracer/get-annotation-labels/", { result: [] }],
    ["/sdk/api/v1/log/model/", {}],
    ["/log/model/", {}],
  ]);
  globalThis.fetch = async (input) => {
    const url = new URL(typeof input === "string" ? input : input.url);
    assert.equal(url.origin, origin);
    assert.ok(responses.has(url.pathname), "Unexpected smoke request: " + url.pathname);
    return new Response(JSON.stringify(responses.get(url.pathname)), {
      status: url.pathname.endsWith("/log/model/") ? 404 : 200,
      headers: { "Content-Type": "application/json" },
    });
  };

  const { APIKeyAuth, Annotation, AnnotationQueue } = require("./src");
  APIKeyAuth.prototype.request = async (config) => {
    assert.equal(config.url, origin + "/health/");
    return { status: 200 };
  };
  Annotation.prototype.getLabels = async () => [{}];
  Annotation.prototype.listProjects = async () => [{}];
  AnnotationQueue.prototype.listLabels = async () => [{}];
  AnnotationQueue.prototype.list = async () => [{}];

  require("./tests/live/smoke.ts");
`;

describe("live smoke after simulation withdrawal", () => {
  it("completes all remaining probes and reports only supported surfaces", () => {
    const result = spawnSync(
      process.execPath,
      ["--require", require.resolve("tsx/cjs"), "--eval", fixture],
      {
        cwd: resolve(__dirname, "../.."),
        encoding: "utf8",
        timeout: 20_000,
        env: {
          ...process.env,
          FI_BASE_URL: "http://sdk-smoke.invalid",
          FI_API_KEY: "fixture-api",
          FI_SECRET_KEY: "fixture-secret",
          FI_LIVE_DATASET_NAME: "",
          TSX_DISABLE_CACHE: "1",
        },
      },
    );

    expect(result.error).toBeUndefined();
    expect({ status: result.status, stderr: result.stderr }).toEqual({
      status: 0,
      stderr: "",
    });
    expect(JSON.parse(result.stdout)).toEqual({
      ok: true,
      labels: 1,
      projects: 1,
      queue_labels: 1,
      queues: 1,
      dataset_id_present: false,
      futureagi_client: {
        current_user_seen: true,
        workspaces: 1,
        datasets: 1,
        sdk_evals_seen: true,
        trace_projects: 1,
        trace_labels_seen: true,
      },
      model_log_route_statuses: {
        "sdk/api/v1/log/model/": 404,
        "log/model/": 404,
      },
    });
  });
});
