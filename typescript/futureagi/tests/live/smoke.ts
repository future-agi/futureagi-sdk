import {
  Annotation,
  AnnotationQueue,
  APIKeyAuth,
  Dataset,
  FutureAGIClient,
  HttpMethod,
} from "../../src";
import type { RequestConfig } from "../../src";

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for the live SDK smoke test`);
  }
  return value;
}

async function firstDatasetName(
  client: APIKeyAuth,
  baseUrl: string,
): Promise<string | undefined> {
  const response = (await client.request({
    method: HttpMethod.GET,
    url: `${baseUrl}/model-hub/develops/get-datasets-names/`,
    timeout: 20_000,
  } as RequestConfig)) as any;
  const datasets = response?.data?.result?.datasets ?? [];
  return datasets[0]?.name;
}

function itemsCount(payload: unknown, keys: string[]): number {
  if (Array.isArray(payload)) {
    return payload.length;
  }
  if (!payload || typeof payload !== "object") {
    return 0;
  }

  const root = payload as Record<string, unknown>;
  const result = root.result;
  const candidates = [
    root,
    result && typeof result === "object"
      ? (result as Record<string, unknown>)
      : undefined,
  ].filter(Boolean) as Record<string, unknown>[];

  for (const candidate of candidates) {
    for (const key of keys) {
      const value = candidate[key];
      if (Array.isArray(value)) {
        return value.length;
      }
      if (value && typeof value === "object") {
        return Object.keys(value).length;
      }
    }
  }
  return 0;
}

async function main(): Promise<void> {
  const baseUrl = requiredEnv("FI_BASE_URL").replace(/\/$/, "");
  const auth = {
    fiApiKey: requiredEnv("FI_API_KEY"),
    fiSecretKey: requiredEnv("FI_SECRET_KEY"),
    fiBaseUrl: baseUrl,
    timeout: Number(process.env.FI_LIVE_TIMEOUT ?? 20) * 1000,
  };

  const raw = new APIKeyAuth(auth);
  const health = (await raw.request({
    method: HttpMethod.GET,
    url: `${baseUrl}/health/`,
    timeout: 10_000,
  } as RequestConfig)) as any;
  if (health.status !== 200) {
    throw new Error(`health check failed with ${health.status}`);
  }

  const annotation = new Annotation(auth);
  const labels = await annotation.getLabels();
  const projects = await annotation.listProjects({ pageSize: 5 });

  const queue = new AnnotationQueue(auth);
  const queueLabels = await queue.listLabels();
  const queues = await queue.list();

  const datasetName =
    process.env.FI_LIVE_DATASET_NAME ?? (await firstDatasetName(raw, baseUrl));
  let datasetId: string | undefined;
  if (datasetName) {
    const dataset = await Dataset.getDatasetConfig(datasetName, auth);
    datasetId = dataset.id;
  }

  const futureagi = new FutureAGIClient({
    apiKey: auth.fiApiKey,
    secretKey: auth.fiSecretKey,
    baseUrl,
  });
  const currentUser = await futureagi.users.current();
  const workspaces = await futureagi.users.workspaces({ limit: 5 });
  const futureagiDatasets = await futureagi.datasets.listNames({
    search_text: process.env.FI_LIVE_DATASET_NAME ?? "sdk-live-dataset",
  });
  const sdkEvals = await futureagi.evals.listSdkEvals();
  const simulationRunTests = await futureagi.simulations.runTests.list({
    limit: 5,
  });
  const activeRunTests = await futureagi.simulations.runTests.active();
  const traceProjects = await futureagi.tracing.projects({ limit: 5 });
  const traceLabels = await futureagi.tracing.annotationLabels();

  const routeStatuses: Record<string, number> = {};
  for (const path of ["sdk/api/v1/log/model/", "log/model/"]) {
    const response = await fetch(`${baseUrl}/${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": auth.fiApiKey,
        "X-Secret-Key": auth.fiSecretKey,
      },
      body: "{}",
      signal: AbortSignal.timeout(10_000),
    });
    routeStatuses[path] = response.status;
  }
  if (Object.values(routeStatuses).some((status) => status !== 404)) {
    throw new Error(
      `model logging route status changed: ${JSON.stringify(routeStatuses)}`,
    );
  }

  await Promise.all([raw.close(), annotation.close(), queue.close()]);

  console.log(
    JSON.stringify(
      {
        ok: true,
        labels: labels.length,
        projects: projects.length,
        queue_labels: queueLabels.length,
        queues: queues.length,
        dataset_id_present: Boolean(datasetId),
        futureagi_client: {
          current_user_seen: Boolean(currentUser),
          workspaces: itemsCount(workspaces, ["workspaces", "data", "items"]),
          datasets: itemsCount(futureagiDatasets, [
            "datasets",
            "data",
            "items",
          ]),
          sdk_evals_seen: Boolean(sdkEvals),
          simulation_run_tests_seen: Boolean(simulationRunTests),
          active_run_tests_seen: Boolean(activeRunTests),
          trace_projects: itemsCount(traceProjects, [
            "projects",
            "data",
            "items",
          ]),
          trace_labels_seen: Boolean(traceLabels),
        },
        model_log_route_statuses: routeStatuses,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
