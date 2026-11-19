import { FutureAGIClient } from "../futureagi-client";

// FA success_response uses boolean true, not the string "success".
const envelope = (result: unknown) => ({ status: true, result });
const page = { count: 0, next: null, previous: null, results: [], total_pages: 1, current_page: 1 };
const monitorPage = { results: [], metadata: { total_rows: 0, page_number: 0, page_size: 30, total_pages: 0 } };
const cases: Array<[string, (client: FutureAGIClient) => Promise<unknown>, unknown, number, HeadersInit?]> = [
  ["alerts.list", c => c.alerts.list(), envelope(monitorPage), 200],
  ["alerts.create", c => c.alerts.create({}), envelope("Example alert created successfully"), 200],
  // DRF retrieve, list and destroy are not success_response overrides.
  ["alerts.get", c => c.alerts.get("id"), { id: "id", name: "Example" }, 200],
  ["alerts.update", c => c.alerts.update("id", {}), envelope({ id: "id", name: "Updated" }), 200],
  ["alerts.delete", c => c.alerts.delete("id"), null, 204],
  ["alerts.metricOptions", c => c.alerts.metricOptions({ project_id: "id" }), envelope([]), 200],
  ["alerts.previewGraph", c => c.alerts.previewGraph({}), envelope({ data: [] }), 200],
  ["alerts.graph", c => c.alerts.graph("id"), envelope({ data: [] }), 200],
  ["alerts.details", c => c.alerts.details("id"), envelope({ id: "id", logs: monitorPage, window_start: null, window_end: null }), 200],
  ["alerts.bulkMute", c => c.alerts.bulkMute({ ids: ["id"] }), envelope({ message: "1 User Alerts have been muted successfully." }), 200],
  ["alerts.logs", c => c.alerts.logs(), page, 200],
  ["alerts.allLogs", c => c.alerts.allLogs(), envelope([{ id: "log" }]), 200],
  ["alerts.log", c => c.alerts.log("log"), { id: "log" }, 200],
  ["alerts.logsForAlert", c => c.alerts.logsForAlert("id"), envelope([{ id: "log" }]), 200],
  ["alerts.resolveLogs", c => c.alerts.resolveLogs({ log_ids: ["log"] }), envelope("1 log entries marked as resolved successfully"), 200],
  // These deletes are HTTP 200 envelopes despite stale Swagger 204 declarations.
  ["annotationQueues.archive", c => c.annotationQueues.archive("id"), envelope({ deleted: true, archived: true, queue_id: "id" }), 200],
  ["datasets.deleteRow", c => c.datasets.deleteRow("id"), envelope("Row deleted successfully"), 200],
  ["datasets.deleteColumn", c => c.datasets.deleteColumn("id", "column"), envelope("Column deleted successfully"), 200],
  ["evals.deleteDatasetUserEval", c => c.evals.deleteDatasetUserEval("id", "eval"), envelope("Eval deleted successfully"), 200],
  ["evals.deleteDatasetTemplateEval", c => c.evals.deleteDatasetTemplateEval("id", "eval"), envelope("Eval deleted successfully"), 200],
  ["experimentsV2.delete", c => c.experimentsV2.delete({ experiment_ids: ["id"] }), envelope({ message: "1 experiments deleted successfully", deleted_count: 1 }), 200],
  // ExtendedPageNumberPagination always includes total_pages and current_page.
  ["annotationLabels.list", c => c.annotationLabels.list(), { ...page, count: 1, results: [{ id: "label", name: "quality" }] }, 200],
  ["scores.labels.list", c => c.scores.labels.list(), { ...page, count: 1, results: [{ id: "label", name: "quality" }] }, 200],
  ["scores.list", c => c.scores.list(), page, 200],
  ["annotationQueues.list", c => c.annotationQueues.list(), page, 200],
  ["annotationQueues.items.list", c => c.annotationQueues.items.list("id"), page, 200],
  ["experimentsV2.list", c => c.experimentsV2.list(), page, 200],
  ["prompts.list", c => c.prompts.list(), page, 200],
  ["prompts.labels.list", c => c.prompts.labels.list(), page, 200],
  ["prompts.versions.list", c => c.prompts.versions.list("id"), page, 200],
  // Neighboring envelopes must not acquire fetch-client {data, request, response} fields.
  ["datasets.list", c => c.datasets.list(), envelope({ table: [], metadata: { total_rows: 0 } }), 200],
  ["experimentsV2.get", c => c.experimentsV2.get("id"), envelope({ id: "id" }), 200],
  ["users.organizationMembers", c => c.users.organizationMembers(), envelope([]), 200],
  ["annotationQueues.progress", c => c.annotationQueues.progress("id"), envelope({}), 200],
  ["evals.getTemplate", c => c.evals.getTemplate("id"), envelope({ id: "id" }), 200],
];

describe("catalog wire response compatibility", () => {
  // Object rows prevent Jest from treating an omitted optional header as a `done` callback.
  test.each(cases.map(([name, invoke, body, status, headers]) => ({ name, invoke, body, status, headers })))(
    "$name preserves the server response shape", async ({ invoke, body, status, headers }) => {
    const fetchMock = jest.fn(async () => status === 204
      ? new Response(null, { status, headers })
      : Response.json(body, { status, headers }));
    const client = new FutureAGIClient({
      apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://api.test", retries: 0,
      fetch: fetchMock as typeof fetch,
    });
    expect(await invoke(client)).toEqual(body);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
