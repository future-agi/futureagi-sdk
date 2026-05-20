import {
  Annotation,
  AnnotationQueue,
  APIKeyAuth,
  Dataset,
  HttpMethod,
} from '../../src';
import type { RequestConfig } from '../../src';

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for the live SDK smoke test`);
  }
  return value;
}

async function firstDatasetName(client: APIKeyAuth, baseUrl: string): Promise<string | undefined> {
  const response = await client.request({
    method: HttpMethod.GET,
    url: `${baseUrl}/model-hub/develops/get-datasets-names/`,
    timeout: 20_000,
  } as RequestConfig) as any;
  const datasets = response?.data?.result?.datasets ?? [];
  return datasets[0]?.name;
}

async function main(): Promise<void> {
  const baseUrl = requiredEnv('FI_BASE_URL').replace(/\/$/, '');
  const auth = {
    fiApiKey: requiredEnv('FI_API_KEY'),
    fiSecretKey: requiredEnv('FI_SECRET_KEY'),
    fiBaseUrl: baseUrl,
    timeout: Number(process.env.FI_LIVE_TIMEOUT ?? 20) * 1000,
  };

  const raw = new APIKeyAuth(auth);
  const health = await raw.request({
    method: HttpMethod.GET,
    url: `${baseUrl}/health/`,
    timeout: 10_000,
  } as RequestConfig) as any;
  if (health.status !== 200) {
    throw new Error(`health check failed with ${health.status}`);
  }

  const annotation = new Annotation(auth);
  const labels = await annotation.getLabels();
  const projects = await annotation.listProjects({ pageSize: 5 });

  const queue = new AnnotationQueue(auth);
  const queueLabels = await queue.listLabels();
  const queues = await queue.list();

  const datasetName = process.env.FI_LIVE_DATASET_NAME ?? await firstDatasetName(raw, baseUrl);
  let datasetId: string | undefined;
  if (datasetName) {
    const dataset = await Dataset.getDatasetConfig(datasetName, auth);
    datasetId = dataset.id;
  }

  const routeStatuses: Record<string, number> = {};
  for (const path of ['sdk/api/v1/log/model/', 'log/model/']) {
    const response = await fetch(`${baseUrl}/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Api-Key': auth.fiApiKey,
        'X-Secret-Key': auth.fiSecretKey,
      },
      body: '{}',
      signal: AbortSignal.timeout(10_000),
    });
    routeStatuses[path] = response.status;
  }
  if (Object.values(routeStatuses).some((status) => status !== 404)) {
    throw new Error(`model logging route status changed: ${JSON.stringify(routeStatuses)}`);
  }

  await Promise.all([raw.close(), annotation.close(), queue.close()]);

  console.log(JSON.stringify({
    ok: true,
    labels: labels.length,
    projects: projects.length,
    queue_labels: queueLabels.length,
    queues: queues.length,
    dataset_id_present: Boolean(datasetId),
    model_log_route_statuses: routeStatuses,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
