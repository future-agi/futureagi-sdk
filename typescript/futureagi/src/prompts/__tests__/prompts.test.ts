import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError, NotFoundError, UnexpectedRedirectError } from "../../_core/errors";
import { PromptsClient } from "..";

function setup(response = new Response(JSON.stringify({ status: true, result: { ok: true } }), { headers: { "Content-Type": "application/json" } })) {
  const fetchMock = jest.fn(async (request: Request) => {
    expect(new URL(request.url).origin).toBe("http://127.0.0.1:9");
    expect(request.headers.get("X-Api-Key")).toBe("fixture-api");
    expect(request.headers.get("X-Secret-Key")).toBe("fixture-secret");
    expect(request.headers.get("X-Test")).toBe("inherited");
    return response;
  });
  const root = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", headers: { "X-Test": "inherited" }, retries: 0, fetch: fetchMock as typeof fetch });
  return { prompts: new PromptsClient(root.generatedClient), fetchMock };
}

type Case = [string, (client: PromptsClient) => unknown, string, string, unknown?, Record<string, string>?];
const cases: Case[] = [
  ["list", p => p.list({ search: "hello & world", limit: 2 }), "GET", "prompt-templates/", undefined, { search: "hello & world", limit: "2" }],
  ["create", p => p.create({ name: "hello", prompt_config: [{ messages: [] }] }), "POST", "prompt-templates/create-draft/", { name: "hello", prompt_config: [{ messages: [] }] }],
  ["get", p => p.get("p1"), "GET", "prompt-templates/p1/"],
  ["update", p => p.update("p1", { description: null }), "PATCH", "prompt-templates/p1/", { description: null }],
  ["delete", p => p.delete("p1"), "DELETE", "prompt-templates/p1/"],
  ["get by version", p => p.getByName("hello & world", { version: "v2" }), "GET", "prompt-labels/get-by-name/", undefined, { name: "hello & world", version: "v2" }],
  ["get by label selector", p => p.getByName("hello & world", { label: "release & review" }), "GET", "prompt-labels/get-by-name/", undefined, { name: "hello & world", label: "release & review" }],
  ["get by label", p => p.getByLabel("hello", "production"), "GET", "prompt-labels/get-by-name/", undefined, { name: "hello", label: "production" }],
  ["versions", p => p.versions.list("p1", { page: 2, limit: 5 }), "GET", "prompt-templates/p1/versions/", undefined, { page: "2", limit: "5" }],
  ["draft", p => p.versions.create("p1", { new_prompts: [{ prompt_config: [] }] }), "POST", "prompt-templates/p1/add-new-draft/", { new_prompts: [{ prompt_config: [] }] }],
  ["commit", p => p.versions.commit("p1", "v2", { message: "release", setDefault: true }), "POST", "prompt-templates/p1/commit/", { version_name: "v2", message: "release", set_default: true, is_draft: false }],
  ["default", p => p.versions.setDefault("hello", "v2"), "POST", "prompt-labels/set-default/", { template_name: "hello", version: "v2" }],
  ["labels list", p => p.labels.list({ page: 2 }), "GET", "prompt-labels/", undefined, { page: "2" }],
  ["label create", p => p.labels.create({ name: "review", type: "custom" }), "POST", "prompt-labels/", { name: "review", type: "custom" }],
  ["label get", p => p.labels.get("l1"), "GET", "prompt-labels/l1/"],
  ["label update", p => p.labels.update("l1", { name: "reviewed" }), "PATCH", "prompt-labels/l1/", { name: "reviewed" }],
  ["label delete", p => p.labels.delete("l1"), "DELETE", "prompt-labels/l1/"],
  ["assign", p => p.labels.assign("p1", "l1", { version: "v2" }), "POST", "prompt-labels/p1/l1/assign-label-by-id/", { version: "v2" }],
  ["remove", p => p.labels.remove("v-id", "l1"), "POST", "prompt-labels/remove/", { version_id: "v-id", label_id: "l1" }],
  ["template labels", p => p.labels.forTemplate("p1"), "GET", "prompt-labels/template-labels/", undefined, { template_id: "p1" }],
];

test.each(cases.map(row => [row] as const))("generated prompt operation %s", async ([_name, call, method, path, body, query = {}]) => {
  const { prompts, fetchMock } = setup();
  await expect(call(prompts)).resolves.toEqual({ ok: true });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const request = fetchMock.mock.calls[0][0];
  const url = new URL(request.url);
  expect(request.method).toBe(method);
  expect(url.pathname).toBe("/model-hub/" + path);
  expect(Object.fromEntries(url.searchParams.entries())).toEqual(query);
  expect(await request.text()).toBe(body === undefined ? "" : JSON.stringify(body));
});

test.each([
  { name: "hello" },
  { name: "hello", prompt_config: [] },
  { name: "hello", prompt_config: { messages: [] } },
])("create needs the first version's config and rejects without a request (%j)", async (body) => {
  const { prompts, fetchMock } = setup();
  await expect(prompts.create(body as never)).rejects.toThrow("prompt_config");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("name-only lookup rejects before any request", async () => {
  const { prompts, fetchMock } = setup();
  await expect(prompts.getByName("hello")).rejects.toBeInstanceOf(BadRequestError);
  expect(fetchMock).not.toHaveBeenCalled();
});

test.each([
  {},
  { version: undefined, label: undefined },
  { version: "" },
  { label: "" },
  { version: " \t" },
  { label: " \t" },
  { version: "v1", label: "prod" },
  { version: "v1", label: "" },
  { version: "", label: "prod" },
  { version: 1 },
  { label: false },
])("lookup requires exactly one nonempty selector before any request (%j)", async (selector) => {
  const { prompts, fetchMock } = setup();
  const result = prompts.getByName("hello", selector as never);
  await expect(result).rejects.toBeInstanceOf(BadRequestError);
  await expect(result).rejects.toMatchObject({
    code: "invalid_prompt_selector",
    message: expect.stringContaining("exactly one of version or label"),
  });
  expect(fetchMock).not.toHaveBeenCalled();
});

test("empty label shortcut rejects before any request", async () => {
  const { prompts, fetchMock } = setup();
  await expect(prompts.getByLabel("hello", "")).rejects.toBeInstanceOf(BadRequestError);
  expect(fetchMock).not.toHaveBeenCalled();
});

test("generated paths encode identifiers", async () => {
  const { prompts, fetchMock } = setup();
  await prompts.labels.get("a/b ?#");
  expect(new URL(fetchMock.mock.calls[0][0].url).pathname).toBe("/model-hub/prompt-labels/a%2Fb%20%3F%23/");
});

test.each([
  [404, { detail: "missing" }, NotFoundError],
  [200, { status: false, result: "bad label" }, BadRequestError],
  [302, {}, UnexpectedRedirectError],
] as const)("prompt errors remain typed (%s)", async (status, payload, error) => {
  const { prompts } = setup(new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json", location: "http://127.0.0.2/private" } }));
  await expect(prompts.get("p1")).rejects.toBeInstanceOf(error);
});

test("retrieved versions have template types and compile without another request", async () => {
  const template = { id: "p1", name: "hello", version: "v2", prompt_config: [{ messages: [{ role: "user", content: "Hello {{name}}" }] }] };
  const { prompts, fetchMock } = setup(new Response(JSON.stringify({ status: true, result: template }), { headers: { "Content-Type": "application/json" } }));
  const fetched = await prompts.getByLabel("hello", "production");
  const version: string | undefined = fetched.version;
  expect(version).toBe("v2");
  expect(fetched.prompt_config?.[0].messages).toEqual(template.prompt_config[0].messages);
  expect(prompts.compile(fetched, { name: "reader" })).toEqual([{ role: "user", content: "Hello reader" }]);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("list keeps DRF page metadata", async () => {
  const page = { count: 5, next: "?page=2", previous: null, results: [{ id: "p1" }] };
  const { prompts } = setup(new Response(JSON.stringify(page), { headers: { "Content-Type": "application/json" } }));
  await expect(prompts.list({ page: 1 })).resolves.toEqual(page);
});

test("compile is local, preserves multimodal structure, and clones inputs", () => {
  const { prompts, fetchMock } = setup();
  const template = { prompt_config: [{ messages: [
    { role: "user", content: [{ type: "text", text: "Hello {{ who }} / {{missing}}" }, { type: "image_url", image_url: { url: "data:example" } }] },
    { type: "placeholder", name: "history" }, { type: "placeholder", name: "unresolved" },
  ] }] };
  const variables = { who: "reader", history: [{ role: "assistant", content: "Welcome {{who}}", tool_calls: [{ id: "call-one" }] }] };
  const before = JSON.stringify([template, variables]);
  const result = prompts.compile(template, variables);
  expect(result).toEqual([
    { role: "user", content: [{ type: "text", text: "Hello reader / {{missing}}" }, { type: "image_url", image_url: { url: "data:example" } }] },
    { role: "assistant", content: "Welcome reader", tool_calls: [{ id: "call-one" }] },
    { type: "placeholder", name: "unresolved" },
  ]);
  (result[1].tool_calls as { id: string }[])[0].id = "changed";
  expect(JSON.stringify([template, variables])).toBe(before);
  expect(fetchMock).not.toHaveBeenCalled();
  expect(() => prompts.compile({})).toThrow("messages list");
  expect(() => prompts.compile({ messages: [{}] })).toThrow("role and content");
  expect(() => prompts.compile({ messages: [{ type: "placeholder", name: "h" }] }, { h: "bad" })).toThrow("lists of chat messages");
});
