import { checkWire, runtime, success, type Case } from "../__fixtures__/contract-runtime";

const prompt: Case = {
  id: "core:prompts.get", adapter: "core", name: "prompts.get", method: "GET",
  path: "/model-hub/prompt-templates/{id}/", path_params: ["id"], content_type: null,
  stream: null, idempotent: false, retry: "http-idempotent", ts_operation: "modelHubPromptTemplatesRead",
};

test.each(["missing", "misroute"])("public prompt %s mutation fails its contract", async mutation => {
  const requests: Request[] = [];
  const subject = runtime(prompt, request => { requests.push(request); return success(prompt); });
  const resource = (subject as any).client.prompts;
  resource.get = mutation === "missing" ? undefined : resource.delete;
  if (mutation === "missing") {
    await expect(subject.call()).rejects.toThrow(/get|callable/);
    expect(requests).toHaveLength(0);
  } else {
    await subject.call();
    expect(requests).toHaveLength(1);
    expect(() => checkWire(prompt, requests[0])).toThrow();
  }
});

test("public prompt uses the real envelope adapter", async () => {
  let payload: unknown = { status: true, result: { marker: "kept" } };
  const subject = runtime(prompt, () => Response.json(payload, { headers: { "X-Request-Id": "contract-envelope" } }));
  await expect(subject.call()).resolves.toEqual({ marker: "kept" });
  payload = { status: false, code: "invalid", result: "refused" };
  await expect(subject.call()).rejects.toMatchObject({ statusCode: 400, code: "invalid", requestId: "contract-envelope" });
});
