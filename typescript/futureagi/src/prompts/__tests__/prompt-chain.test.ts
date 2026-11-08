import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../../_core/errors";

type Version = { config: Record<string, unknown>; draft: boolean; labels: Set<string> };
type Template = { name: string; versions: Map<string, Version> };

const greeting = {
  messages: [{ role: "user", content: [{ type: "text", text: "Hello {{name}}" }] }],
  configuration: { model: "test-model" },
};

const json = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
const ok = (result: unknown) => json({ status: true, result });
const refused = (result: string) => json({ status: false, result }, 400);

/** Loopback stand-in for the prompt routes, keeping templates, versions and labels in memory. */
function promptRoutes() {
  const templates = new Map<string, Template>();
  const labels = new Map<string, string>();
  const fetchMock = jest.fn(async (request: Request) => {
    const url = new URL(request.url);
    const route = url.pathname.replace(/^\/model-hub\//, "").replace(/\/$/, "").split("/");
    const text = await request.text();
    const body = text ? JSON.parse(text) : {};
    const last = route[route.length - 1];
    if (route.join("/") === "prompt-templates/create-draft") {
      const id = `t${templates.size + 1}`;
      templates.set(id, { name: body.name, versions: new Map([["v1", { config: body.prompt_config[0], draft: true, labels: new Set() }]]) });
      return ok({ id, name: body.name, created_version: "v1", template_version: "v1", is_draft: true });
    }
    if (route[0] === "prompt-templates" && last === "add-new-draft") {
      const versions = templates.get(route[1])!.versions;
      const made = body.new_prompts.map((prompt: { prompt_config: Record<string, unknown>[] }) => {
        const name = `v${versions.size + 1}`;
        versions.set(name, { config: prompt.prompt_config[0], draft: true, labels: new Set() });
        return { template_version: name, is_draft: true };
      });
      return ok(made);
    }
    if (route[0] === "prompt-templates" && last === "commit") {
      const version = templates.get(route[1])!.versions.get(body.version_name);
      if (!version) return refused("Prompt Version Not Found");
      version.draft = body.is_draft;
      return ok(`Commit for ${body.version_name} has been added`);
    }
    if (route.join("/") === "prompt-labels") {
      const id = `l${labels.size + 1}`;
      labels.set(id, body.name);
      return json({ id, ...body }, 201);
    }
    if (route[0] === "prompt-labels" && last === "assign-label-by-id") {
      const [, templateId, labelId] = route;
      const versions = templates.get(templateId)!.versions;
      if (!versions.has(body.version)) return refused(`No version '${body.version}' found`);
      for (const version of versions.values()) version.labels.delete(labelId);
      versions.get(body.version)!.labels.add(labelId);
      return ok({ template_id: templateId, version: body.version, label_id: labelId, label_name: labels.get(labelId), moved_from_versions: [] });
    }
    if (route.join("/") === "prompt-labels/get-by-name") {
      const name = url.searchParams.get("name");
      const label = (url.searchParams.get("label") ?? "").toLowerCase();
      const [id, template] = [...templates].find(([, value]) => value.name === name)!;
      for (const [version, value] of template.versions) {
        if ([...value.labels].some((item) => labels.get(item)?.toLowerCase() === label)) {
          return ok({ id, name, version, is_draft: value.draft, prompt_config: [value.config] });
        }
      }
      return refused(`No version found for label '${label}'`);
    }
    return json({ detail: `no route for ${request.method} ${url.pathname}` }, 404);
  });
  const client = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", retries: 0, fetch: fetchMock as typeof fetch });
  return { prompts: client.prompts, fetchMock, templates };
}

test("a prompt is created with its first version, committed, labelled, fetched by label and compiled", async () => {
  const { prompts, fetchMock, templates } = promptRoutes();
  const created = await prompts.create({ name: "greeting", prompt_config: [greeting] });
  const first: string = created.created_version;
  expect(templates.get(created.id)?.versions.get(first)?.config).toEqual(greeting);
  await prompts.versions.commit(created.id, first, { message: "first" });
  const label = await prompts.labels.create({ name: "production", type: "custom" });
  const assigned = await prompts.labels.assign(created.id, String(label.id), { version: first });
  expect(assigned.version).toBe(first);
  const fetched = await prompts.getByLabel("greeting", "production");
  expect([fetched.version, fetched.is_draft]).toEqual([first, false]);
  expect(prompts.compile(fetched, { name: "reader" })).toEqual([{ role: "user", content: [{ type: "text", text: "Hello reader" }] }]);
  expect(fetchMock.mock.calls.map(([request]) => `${request.method} ${new URL(request.url).pathname}`)).toEqual([
    "POST /model-hub/prompt-templates/create-draft/",
    `POST /model-hub/prompt-templates/${created.id}/commit/`,
    "POST /model-hub/prompt-labels/",
    `POST /model-hub/prompt-labels/${created.id}/${label.id}/assign-label-by-id/`,
    "GET /model-hub/prompt-labels/get-by-name/",
  ]);
});

test("a later version is drafted, committed and takes the label", async () => {
  const { prompts } = promptRoutes();
  const created = await prompts.create({ name: "greeting", prompt_config: [greeting] });
  const revised = { ...greeting, messages: [{ role: "user", content: "Hi {{name}}" }] };
  const drafts = await prompts.versions.create(created.id, { new_prompts: [{ prompt_config: [revised] }] });
  const later = drafts[0].template_version;
  expect(later).not.toBe(created.created_version);
  const label = await prompts.labels.create({ name: "production", type: "custom" });
  await prompts.labels.assign(created.id, String(label.id), { version: created.created_version });
  await prompts.versions.commit(created.id, later);
  await prompts.labels.assign(created.id, String(label.id), { version: later });
  const fetched = await prompts.getByLabel("greeting", "production");
  expect(fetched.version).toBe(later);
  expect(prompts.compile(fetched, { name: "reader" })).toEqual([{ role: "user", content: "Hi reader" }]);
  await expect(prompts.versions.commit(created.id, "v9")).rejects.toBeInstanceOf(BadRequestError);
});
