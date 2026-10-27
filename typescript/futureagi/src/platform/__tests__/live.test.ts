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

live("platform client against a live backend", () => {
  jest.setTimeout(120_000);
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
    await expect(client.datasets.get(ds.dataset_id!)).rejects.toBeInstanceOf(BadRequestError); // backend answers 400, not 404
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

  test("knowledge bases: multipart create, update, files, delete", async () => {
    const kb = await client.knowledgeBases.create({ name: name("kb"), file: [{ name: "notes.txt", data: "hello from typescript" }] });
    try {
      expect(kb.file_ids).toHaveLength(1);
      // Backend: an update that adds files is refused (400) while an earlier upload is still being
      // processed, and the refused update stores its file anyway. Wait for the worker.
      const processed = async () => (await client.knowledgeBases.files.list({ kb_id: kb.kb_id! })).table_data!.every((f) => f!.status !== "Processing");
      expect(await waitUntil(processed)).toBe(true);
      const updated = await client.knowledgeBases.update({ kb_id: kb.kb_id!, name: `${kb.kb_name}-u`, file: [{ name: "more.txt", data: "second file" }] });
      expect(updated.name).toBe(`${kb.kb_name}-u`);
      expect((await client.knowledgeBases.files.list({ kb_id: kb.kb_id! })).total_rows).toBe(2);
      expect(await waitUntil(processed)).toBe(true); // a file being processed is not deleted
      expect(await client.knowledgeBases.files.delete({ kb_id: kb.kb_id!, file_ids: [kb.file_ids![0]!] })).toBeTruthy();
      expect(await waitUntil(async () => (await client.knowledgeBases.files.list({ kb_id: kb.kb_id! })).total_rows === 1)).toBe(true);
    } finally {
      await client.knowledgeBases.delete({ kb_ids: [kb.kb_id!] });
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
