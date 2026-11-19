import * as rootExports from "../index";
import { FutureAGIClient, KnowledgeBasesClient, PromptsClient, ScoresClient } from "../index";
import { CoreServerError } from "../_core/__fixtures__/platform";

test("root client registers core namespaces and copies retain configuration", async () => {
  const fetchMock = jest.fn(async (request: Request) => {
    expect(new URL(request.url).origin).toBe("http://127.0.0.1:9");
    expect(request.headers.get("X-Api-Key")).toBe("fixture-api");
    expect(request.headers.get("X-Secret-Key")).toBe("fixture-secret");
    expect(request.headers.get("X-Test")).toBe("inherited");
    return new Response(JSON.stringify({ status: true, result: { ok: true } }), { headers: { "Content-Type": "application/json" } });
  });
  const root = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", headers: { "X-Test": "inherited" }, fetch: fetchMock as typeof fetch });
  expect(root.prompts).toBeInstanceOf(PromptsClient);
  expect(root.knowledgeBases).toBeInstanceOf(KnowledgeBasesClient);
  expect(root.scores).toBeInstanceOf(ScoresClient);
  expect(root.annotationLabels).toBe(root.scores.labels);
  const clone = root.withOptions({ timeoutMs: 2000, retries: 0 });
  expect(clone.annotationLabels).toBe(clone.scores.labels);
  for (const name of ["prompts", "knowledgeBases", "scores", "annotationLabels"] as const) {
    expect(clone[name]).not.toBe(root[name]);
    await expect(clone[name].list()).resolves.toEqual({ ok: true });
  }
  expect(fetchMock).toHaveBeenCalledTimes(4);
});

test("namespace POST create does not retry after a server failure", async () => {
  const fetchMock = jest.fn(async () => new Response(JSON.stringify({ detail: "unavailable" }), { status: 503, headers: { "Content-Type": "application/json" } }));
  const client = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", retries: 2, fetch: fetchMock as typeof fetch });
  await expect(client.prompts.create({ name: "hello", prompt_config: [{ messages: [] }] })).rejects.toBeInstanceOf(CoreServerError);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("namespace resource classes have root names distinct from the legacy prompt labels", () => {
  const names = Object.keys(rootExports);
  expect(names).toEqual(expect.arrayContaining(["PromptLabelsClient", "PromptVersionsClient", "KnowledgeBaseDocumentsClient"]));
  expect(names).not.toContain("PromptLabels");
  expect(names).not.toContain("PromptVersions");
  expect(names).not.toContain("KnowledgeBaseDocuments");
});
