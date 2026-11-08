import { FutureAGIClient } from "../../futureagi-client";
import { PermissionDeniedError } from "../../_core/errors";
import { KnowledgeBasesClient } from "..";

function setup(response = new Response(JSON.stringify({ status: true, result: { ok: true } }), { headers: { "Content-Type": "application/json" } })) {
  const fetchMock = jest.fn(async (request: Request) => {
    expect(new URL(request.url).origin).toBe("http://127.0.0.1:9");
    expect(request.headers.get("X-Api-Key")).toBe("fixture-api");
    expect(request.headers.get("X-Secret-Key")).toBe("fixture-secret");
    return response;
  });
  const root = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", retries: 0, fetch: fetchMock as typeof fetch });
  return { kb: new KnowledgeBasesClient(root.generatedClient), fetchMock };
}

type Case = [string, (client: KnowledgeBasesClient) => unknown, string, string, unknown?];
const cases: Case[] = [
  ["create", k => k.create("docs"), "POST", "knowledge-base/", { name: "docs" }],
  ["list", k => k.list({ search: "docs & notes" }), "GET", "knowledge-base/list/"],
  ["update", k => k.update("kb1", { name: "new" }), "PATCH", "knowledge-base/", { name: "new", kb_id: "kb1" }],
  ["delete", k => k.delete("kb1"), "DELETE", "knowledge-base/", { kb_ids: ["kb1"] }],
  ["documents list", k => k.documents.list("kb1", { page_number: 0, page_size: 2 }), "POST", "knowledge-base/files/", { page_number: 0, page_size: 2, kb_id: "kb1" }],
  ["documents delete", k => k.documents.delete("kb1", ["guide.txt"]), "DELETE", "knowledge-base/files/", { kb_id: "kb1", file_names: ["guide.txt"] }],
];

test.each(cases.map(row => [row] as const))("generated knowledge-base operation %s", async ([name, call, method, path, body]) => {
  const { kb, fetchMock } = setup();
  await expect(call(kb)).resolves.toEqual({ ok: true });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const request = fetchMock.mock.calls[0][0];
  expect(request.method).toBe(method);
  expect(new URL(request.url).pathname).toBe("/model-hub/" + path);
  expect(await request.text()).toBe(body === undefined ? "" : JSON.stringify(body));
  if (name === "list") expect(new URL(request.url).searchParams.get("search")).toBe("docs & notes");
});

test("text upload is multipart, carries credentials and preserves UTF-8", async () => {
  const { kb, fetchMock } = setup();
  await kb.documents.addText("kb1", "guide.txt", "Welcome café");
  const request = fetchMock.mock.calls[0][0];
  expect(request.method).toBe("PATCH");
  expect(new URL(request.url).pathname).toBe("/model-hub/knowledge-base/");
  expect(request.headers.get("Content-Type")).toMatch(/^multipart\/form-data; boundary=/);
  const form = await request.formData();
  expect(form.get("kb_id")).toBe("kb1");
  const file = form.get("file") as File;
  expect(file.name).toBe("guide.txt");
  expect(file.type).toBe("text/plain");
  expect(await file.text()).toBe("Welcome café");
});

test.each(["../guide.txt", "a\\b.txt", "x\r\ny.txt", "x\0.txt", "guide.pdf", ""])("invalid filename is never sent: %s", async (name) => {
  const { kb, fetchMock } = setup();
  await expect(kb.documents.addText("kb1", name, "hello")).rejects.toThrow(TypeError);
  expect(fetchMock).not.toHaveBeenCalled();
});

test("empty document delete is never sent", async () => {
  const { kb, fetchMock } = setup();
  await expect(kb.documents.delete("kb1", [])).rejects.toThrow("at least one filename");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("knowledge-base permission errors retain request ids", async () => {
  const { kb } = setup(new Response(JSON.stringify({ detail: "denied" }), { status: 403, headers: { "Content-Type": "application/json", "x-request-id": "kb-request" } }));
  const error = await kb.delete("foreign-kb").catch((value: unknown) => value);
  expect(error).toBeInstanceOf(PermissionDeniedError);
  expect(error).toMatchObject({ requestId: "kb-request" });
});
