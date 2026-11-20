// Against a real backend (FI_BASE_URL), no mocks. Skipped unless FI_API_KEY, FI_SECRET_KEY
// and FI_BASE_URL are set, or `.env.local` at the repository root provides them
// (`python sdkgen/local_api_key.py` writes it). Run with `pnpm test:live`.
//
// The Python suite calls every catalog operation; this one proves the TypeScript transport
// and the generated code on the paths that differ by surface: JSON and multipart bodies,
// path/query encoding, each pagination style, envelope unwrapping, typed errors, and the
// hand-written `spans.ingest`.

import { existsSync, readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";

import { Client } from "../client";
import { APIError, BadRequestError, NotFoundError } from "../errors";
import type { SQLExecution } from "../models";
import type { RequestOptions } from "../transport";

const ENV_FILE = join(__dirname, "..", "..", "..", "..", "..", ".env.local");
if (existsSync(ENV_FILE)) {
  for (const line of readFileSync(ENV_FILE, "utf8").split("\n")) {
    const [key, ...rest] = line.split("=");
    if (key && rest.length && process.env[key.trim()] === undefined) {
      process.env[key.trim()] = rest.join("=").trim();
    }
  }
}
const configured = Boolean(process.env.FI_API_KEY && process.env.FI_SECRET_KEY && process.env.FI_BASE_URL);
if (!configured && process.env.FI_E2E_REQUIRED) {
  throw new Error("FI_E2E_REQUIRED is set but no backend is configured: run sdkgen/local_api_key.py (writes .env.local)");
}
const live = configured ? describe : describe.skip;

const name = (prefix: string) => `sdk-ts-${prefix}-${randomUUID().slice(0, 8)}`;

/** Call fn; resolve to null instead of throwing for the listed HTTP statuses. */
async function allow<T>(fn: () => Promise<T>, ...statuses: number[]): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof APIError && statuses.includes(error.status)) {
      return null;
    }
    throw error;
  }
}

const SQL_TOTAL_BUDGET_MS = 150_000;
const SQL_REQUEST_TIMEOUT_CAP_MS = 60_000;
const SQL_CLEANUP_BUDGET_MS = 10_000;

/** Poll a backend state change made by a background worker. */
async function waitUntil(predicate: () => Promise<boolean>, ms = 20_000): Promise<boolean> {
  const deadline = Date.now() + ms;
  while (!(await predicate())) {
    if (Date.now() > deadline) {
      return false;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return true;
}

/** Return a positive, bounded request budget without allowing a retry to exceed the test deadline. */
function sqlRequestOptions(deadline: number): RequestOptions {
  const remaining = deadline - Date.now();
  if (!Number.isFinite(remaining) || remaining <= 0) {
    throw new Error("SQL live-test deadline exceeded");
  }
  return { timeout: Math.min(remaining, SQL_REQUEST_TIMEOUT_CAP_MS), maxRetries: 0 };
}

/** Poll SQL until it is terminal, charging every request and wait to the caller's deadline. */
async function pollSqlResult(client: Client, jobId: string, projectId: string, deadline: number): Promise<SQLExecution> {
  let state = "not polled";
  while (Date.now() < deadline) {
    const page = await client.sql.getResult(
      jobId,
      { project_id: projectId, offset: 0, limit: 1 },
      sqlRequestOptions(deadline),
    );
    state = page.state ?? "unknown";
    if (state === "succeeded" || state === "failed" || state === "cancelled") {
      return page;
    }
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, Math.min(500, remaining)));
  }
  throw new Error(`SQL job ${jobId} did not finish in 150s: ${state}`);
}

function terminalSqlState(state: string | null | undefined): boolean {
  return state === "succeeded" || state === "failed" || state === "cancelled";
}

/** Try cancellation repeatedly for a short, independent cleanup window. */
async function cleanupSqlJob(client: Client, jobId: string, projectId: string): Promise<void> {
  const deadline = Date.now() + SQL_CLEANUP_BUDGET_MS;
  let state: string | null | undefined;
  while (Date.now() < deadline) {
    const result = await client.sql.cancel(jobId, { project_id: projectId }, sqlRequestOptions(deadline));
    state = result.state;
    if (terminalSqlState(state)) {
      if (state !== "cancelled") {
        console.warn(`PENDING active SQL cancellation: cleanup observed terminal state ${state}`);
      }
      return;
    }
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, Math.min(250, remaining)));
  }
  throw new Error(`SQL job ${jobId} remained ${state ?? "unknown"} after bounded cleanup`);
}

/** Poll the fixture's span index using the same total deadline as the SQL job. */
async function waitUntilSql(predicate: (options: RequestOptions) => Promise<boolean>, deadline: number): Promise<boolean> {
  while (Date.now() < deadline) {
    if (await predicate(sqlRequestOptions(deadline))) {
      return true;
    }
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      return false;
    }
    await new Promise((resolve) => setTimeout(resolve, Math.min(250, remaining)));
  }
  return false;
}

async function createSqlFixture(client: Client, deadline: number): Promise<{ projectId: string; start: string; end: string; count: number }> {
  const projectName = name("sql");
  const now = Date.now() * 1_000_000;
  const traceId = randomUUID().replace(/-/g, "");
  const spans = ["root", "child"].map((role) => ({
    project_name: projectName,
    project_type: "observe",
    trace_id: traceId,
    span_id: randomUUID().replace(/-/g, "").slice(0, 16),
    name: `sql-${role}`,
    start_time: now - 2_000_000_000,
    end_time: now - 1_000_000_000,
    latency: 1000,
    status: "OK",
    attributes: { "gen_ai.span.kind": "LLM", "session.id": "sdk-ts-sql-session" },
  }));
  const ids: string[] = [];
  for (const span of spans) {
    ids.push(...((await client.spans.ingest([span], sqlRequestOptions(deadline))).ids ?? []));
  }
  expect(ids).toHaveLength(spans.length);
  const projects = (await client.projects.list({ name: projectName }, sqlRequestOptions(deadline))) as { projects: Array<{ id: string }> };
  expect(projects.projects).toHaveLength(1);
  const projectId = projects.projects[0]!.id;
  expect(await waitUntilSql(async (options) => {
    const page = (await client.spans.list({ project_id: projectId }, options)) as { table?: unknown[] };
    return page.table?.length === spans.length;
  }, deadline)).toBe(true);
  return {
    projectId,
    start: new Date(Math.floor(now / 1_000_000) - 60_000).toISOString(),
    end: new Date().toISOString(),
    count: spans.length,
  };
}

live("platform client against a live backend", () => {
  jest.setTimeout(180_000);
  // Built in beforeAll: jest evaluates a skipped describe's body too, and the
  // constructor throws without credentials.
  let client: Client;
  beforeAll(() => {
    client = new Client({ timeout: 60_000 });
  });

  test("context", async () => {
    const me = await client.account.whoami();
    expect(me.email).toBeTruthy();
    const workspaces = await client.workspaces.list();
    expect(workspaces.workspaces?.length).toBeGreaterThan(0);
    expect((await client.workspaces.get(workspaces.workspaces![0]!.id!)).workspaces).toBeTruthy();
  });

  test("datasets: create, columns, rows (beta), read, paginate, delete", async () => {
    const warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    const ds = await client.datasets.create({ new_dataset_name: name("ds") });
    try {
      const columns = await client.datasets.columns.add(ds.dataset_id!, { new_columns_data: [{ name: "question", data_type: "text" }, { name: "answer", data_type: "text" }] });
      expect(columns.data).toHaveLength(2);
      await client.datasets.rows.add(ds.dataset_id!, {
        rows: Array.from({ length: 3 }, (_, i) => ({ cells: [{ column_name: "question", value: `${i}+${i}?` }, { column_name: "answer", value: String(2 * i) }] })),
      });
      const table = await client.datasets.get(ds.dataset_id!);
      expect(table.column_config).toBeTruthy();
      const names = await client.datasets.listNames();
      expect(names.datasets?.map((d) => d!.dataset_id)).toContain(ds.dataset_id);
      const page = await client.datasets.list({ search_text: ds.dataset_name ?? undefined, page_size: 5 }).firstPage();
      expect(page.number).toBe(0);
      const all = await client.datasets.list({ page_size: 2 }).toArray(3); // total_pages style, first page 0
      expect(all.length).toBeGreaterThan(0);
      await client.datasets.evals.stats(ds.dataset_id!);
    } finally {
      expect(await client.datasets.delete({ dataset_ids: [ds.dataset_id!] })).toBeTruthy();
      warn.mockRestore();
    }
    const gone = await client.datasets.get(ds.dataset_id!).catch((e) => e);
    // A deleted dataset is not found: newer backends answer 404, older ones 400.
    expect(gone instanceof NotFoundError || gone instanceof BadRequestError).toBe(true);
    expect(gone.status).toBe(gone instanceof NotFoundError ? 404 : 400);
  });

  test("datasets: multipart upload from bytes", async () => {
    const started = await client.datasets.createFromFile({
      file: { name: "qa.csv", data: "question,answer\n1+1?,2\n2+2?,4\n" },
      new_dataset_name: name("csv"),
      model_type: "GenerativeLLM",
    });
    try {
      expect(started.dataset_id).toBeTruthy();
      expect((await client.datasets.get(started.dataset_id!)).column_config).toBeTruthy();
    } finally {
      await allow(() => client.datasets.delete({ dataset_ids: [started.dataset_id!] }), 400, 404);
    }
  });

  test("prompts: lifecycle, `next` pagination, drafts and labels", async () => {
    const created = await client.prompts.create({ name: name("prompt"), description: "sdk ts test" });
    try {
      expect((await client.prompts.get(created.id!)).name).toBe(created.name);
      expect((await client.prompts.update(created.id!, { description: "updated" })).description).toBe("updated");
      expect((await client.prompts.list({ search: created.name! }).toArray()).map((p) => p.id)).toEqual([created.id]);
      const versions = (await client.prompts.versions.list(created.id!).toArray()) as Array<{ template_version: string }>;
      expect(versions[0]!.template_version).toBe("v1");
    } finally {
      await allow(() => client.prompts.delete(created.id!), 400, 404);
    }

    const draft = await client.prompts.createDraft({
      name: name("draft"),
      prompt_config: [{ messages: [{ role: "user", content: [{ type: "text", text: "Say hi to {{name}}" }] }], configuration: { model: "gpt-4o-mini" }, placeholders: [] }],
      variable_names: { name: "world" },
      placeholders: {},
    });
    try {
      const committed = await client.prompts.commit(draft.id!, { version_name: "v1", message: "from ts" });
      expect(typeof committed).toBe("string"); // untyped: the server answers with a message
      const versions = (await client.prompts.versions.list(draft.id!).toArray()) as Array<{ id: string; template_version: string }>;
      const v1 = versions.find((v) => v.template_version === "v1")!;
      expect((await client.prompts.getByName({ name: draft.name! }) as { id: string }).id).toBe(draft.id);
      const label = await client.prompts.labels.create({ name: name("lbl"), type: "custom" });
      try {
        await client.prompts.labels.assign(draft.id!, label.id!, { version: "v1" });
        expect(((await client.prompts.labels.getTemplate({ name: draft.name!, label: label.name! })) as { id: string }).id).toBe(draft.id);
        await client.prompts.labels.remove({ label_id: label.id!, version_id: v1.id });
      } finally {
        await allow(() => client.request("DELETE", `/model-hub/prompt-labels/${label.id}/`), 400, 404);
      }
    } finally {
      await allow(() => client.prompts.delete(draft.id!), 400, 404);
    }
  });

  test("spans.ingest (hand-written) then traces and projects", async () => {
    const project = name("proj");
    const now = Date.now() * 1_000_000;
    const span = {
      project_name: project, project_type: "observe", trace_id: randomUUID().replace(/-/g, ""), span_id: randomUUID().replace(/-/g, "").slice(0, 16),
      name: "chat", start_time: now - 2_000_000_000, end_time: now - 1_000_000_000, latency: 1000, status: "OK",
      attributes: { "gen_ai.span.kind": "LLM", "input.value": "What is 2+2?", "output.value": "4", "session.id": "sdk-ts-session" },
    };
    const { ids } = await client.spans.ingest([span]);
    expect(ids).toHaveLength(1);
    const projects = (await client.projects.list({ name: project })) as { projects: Array<{ id: string }> };
    expect(projects.projects).toHaveLength(1);
    expect((await client.projects.get(projects.projects[0]!.id)).id).toBe(projects.projects[0]!.id);
    // Served from ClickHouse, which fills asynchronously after ingestion: the page exists, rows may not yet.
    const traces = await client.traces.list({ project_id: projects.projects[0]!.id });
    expect(traces.metadata).toBeTruthy();
  });

  test("sql: owned fixture, default reuse, pages, and bounded cancellation", async () => {
    // Start the budget before fixture setup so ingestion/indexing cannot add another full poll window.
    const deadline = Date.now() + SQL_TOTAL_BUDGET_MS;
    let ownedJobId: string | undefined;
    let ownedProjectId: string | undefined;
    let primaryFailed = false;
    try {
      const fixture = await createSqlFixture(client, deadline);
      ownedProjectId = fixture.projectId;
      const catalog = await client.sql.getCatalog({ project_id: fixture.projectId }, sqlRequestOptions(deadline));
      expect(catalog.max_window_days).toBeGreaterThanOrEqual(1);

      // Omitting reuse exercises the server default instead of forcing the false branch.
      const job = await client.sql.run({
        project_id: fixture.projectId,
        sql: "SELECT name FROM spans ORDER BY name",
        start: fixture.start,
        end: fixture.end,
      }, sqlRequestOptions(deadline));
      ownedJobId = job.id ?? undefined;
      expect(job.id).toBeTruthy();
      expect(job.project_id).toBe(fixture.projectId);
      const first = await pollSqlResult(client, job.id!, fixture.projectId, deadline);
      // A returned terminal snapshot is no longer an active owned job, even if a later assertion fails.
      ownedJobId = undefined;
      expect(first.state).toBe("succeeded");
      expect(first.result?.rows).toHaveLength(1);
      expect(first.result?.has_more).toBe(true);
      expect(first.result?.next_offset).toBeDefined();
      const second = await client.sql.getResult(job.id!, {
        project_id: fixture.projectId,
        offset: first.result!.next_offset!,
        limit: 1,
      }, sqlRequestOptions(deadline));
      expect(second.state).toBe("succeeded");
      expect(second.result?.rows).toHaveLength(1);
      expect(second.result?.has_more).toBe(false);
      const completedCancel = await client.sql.cancel(job.id!, { project_id: fixture.projectId }, sqlRequestOptions(deadline));
      expect(completedCancel.id).toBe(job.id);
      expect(completedCancel.state).toBe("succeeded");

      const active = await client.sql.run({
        project_id: fixture.projectId,
        sql: "SELECT name FROM spans ORDER BY name",
        start: fixture.start,
        end: fixture.end,
        reuse: false,
      }, sqlRequestOptions(deadline));
      ownedJobId = active.id ?? undefined;
      expect(active.id).toBeTruthy();
      if (terminalSqlState(active.state)) {
        // The fast backend may finish before cancel is sent; do not call that in-flight cancellation.
        console.warn(`PENDING active SQL cancellation: fixture job completed as ${active.state}`);
        ownedJobId = undefined;
        return;
      }
      const cancelled = await client.sql.cancel(active.id!, { project_id: fixture.projectId }, sqlRequestOptions(deadline));
      if (terminalSqlState(cancelled.state)) {
        ownedJobId = undefined;
      }
      if (cancelled.state !== "cancelled") {
        console.warn(`PENDING active SQL cancellation: job reached ${cancelled.state ?? "unknown"} before cancel`);
        return;
      }
      expect(cancelled.id).toBe(active.id);
      expect(cancelled.project_id).toBe(fixture.projectId);
    } catch (error) {
      primaryFailed = true;
      throw error;
    } finally {
      if (ownedJobId && ownedProjectId) {
        try {
          await cleanupSqlJob(client, ownedJobId, ownedProjectId);
        } catch (cleanupError) {
          if (primaryFailed) {
            console.warn(`PENDING SQL cleanup after primary failure: ${cleanupError instanceof Error ? cleanupError.message : String(cleanupError)}`);
          } else {
            throw cleanupError;
          }
        }
      }
    }
  });

  test("annotation labels and queues", async () => {
    const ds = await client.datasets.create({ new_dataset_name: name("qds") });
    const label = await client.annotations.labels.create({ name: name("label"), type: "text", settings: { placeholder: "notes", max_length: 200, min_length: 0 } });
    try {
      expect((await client.annotations.labels.list().toArray()).some((l) => l.id === label.id)).toBe(true);
      const queue = await client.annotationQueues.create({ name: name("queue"), label_ids: [label.id!] }, { extraBody: { dataset: ds.dataset_id } });
      try {
        expect((await client.annotationQueues.update(queue.id!, { description: "ts" })).description).toBe("ts");
        expect((await client.annotationQueues.progress(queue.id!)).total).toBe(0);
        expect((await client.annotationQueues.list({ search: queue.name! }).toArray()).map((q) => q.id)).toEqual([queue.id]);
      } finally {
        await client.annotationQueues.delete(queue.id!);
      }
    } finally {
      await client.annotations.labels.delete(label.id!);
      await allow(() => client.datasets.delete({ dataset_ids: [ds.dataset_id!] }), 400, 404);
    }
  });

  test("knowledge bases: create, get, list, update, delete on one store", async () => {
    const kb = await client.knowledgeBases.create({ name: name("kb"), chunk_size: 256 });
    try {
      expect((await client.knowledgeBases.get(kb.id!)).name).toBe(kb.name); // the id a create returns is one get finds
      expect((await client.knowledgeBases.list({ search: kb.name! }).toArray()).map((k) => k.id)).toContain(kb.id);
      expect((await client.knowledgeBases.update(kb.id!, { name: `${kb.name}-u` })).name).toBe(`${kb.name}-u`);
    } finally {
      await client.knowledgeBases.delete(kb.id!);
    }
    await expect(client.knowledgeBases.get(kb.id!)).rejects.toThrow(NotFoundError);
  });

  test("file knowledge bases: multipart create, update, files, delete", async () => {
    const kb = await client.fileKnowledgeBases.create({ name: name("kb"), file: [{ name: "notes.txt", data: "hello from typescript" }] });
    try {
      expect(kb.file_ids).toHaveLength(1);
      expect((await client.fileKnowledgeBases.listNames()).table_data!.map((k) => k!.id)).toContain(kb.kb_id);
      // Backend: an update that adds files is refused (400) while an earlier upload is still being
      // processed, and the refused update stores its file anyway. Wait for the worker.
      const processed = async () => (await client.fileKnowledgeBases.files.list({ kb_id: kb.kb_id! })).table_data!.every((f) => f!.status !== "Processing");
      expect(await waitUntil(processed)).toBe(true);
      const updated = await client.fileKnowledgeBases.update({ kb_id: kb.kb_id!, name: `${kb.kb_name}-u`, file: [{ name: "more.txt", data: "second file" }] });
      expect(updated.name).toBe(`${kb.kb_name}-u`);
      expect((await client.fileKnowledgeBases.files.list({ kb_id: kb.kb_id! })).total_rows).toBe(2);
      expect(await waitUntil(processed)).toBe(true); // a file being processed is not deleted
      expect(await client.fileKnowledgeBases.files.delete({ kb_id: kb.kb_id!, file_ids: [kb.file_ids![0]!] })).toBeTruthy();
      expect(await waitUntil(async () => (await client.fileKnowledgeBases.files.list({ kb_id: kb.kb_id! })).total_rows === 1)).toBe(true);
    } finally {
      await client.fileKnowledgeBases.delete({ kb_ids: [kb.kb_id!] });
    }
  });

  test("dashboards: a description-only update is a partial update, and a create returns the detail", async () => {
    const dashboard = await client.dashboards.create({ name: name("dash") });
    try {
      expect(dashboard.id).toBeTruthy(); // typed: the response is the dashboard detail, not the create input
      const updated = await client.dashboards.update(dashboard.id!, { description: "description only" });
      expect(updated.description).toBe("description only");
      expect(updated.name).toBe(dashboard.name);
    } finally {
      await client.dashboards.delete(dashboard.id!);
    }
  });

  test("typed errors from the backend", async () => {
    const missing = await client.prompts.get(randomUUID()).catch((e) => e);
    expect(missing instanceof NotFoundError || missing instanceof BadRequestError).toBe(true); // backend answers 400 for unknown ids
    expect(missing.status).toBe(missing instanceof NotFoundError ? 404 : 400);
    const error = await client.datasets.create({ new_dataset_name: "" }).catch((e) => e);
    expect(error).toBeInstanceOf(BadRequestError);
    expect(error.message).toContain("400");
    expect(error.detail).toBeTruthy();
  });
});

test("live tests are configured or skipped explicitly", () => {
  if (!configured) {
    console.log("platform live tests skipped: set FI_API_KEY, FI_SECRET_KEY and FI_BASE_URL (or write .env.local)");
  }
});
