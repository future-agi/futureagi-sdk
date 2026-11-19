import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError } from "../../_core/errors";
import { ScoresClient } from "..";

function setup(response = new Response(JSON.stringify({ status: true, result: { ok: true } }), { headers: { "Content-Type": "application/json" } })) {
  const fetchMock = jest.fn(async (request: Request) => {
    expect(new URL(request.url).origin).toBe("http://127.0.0.1:9");
    expect(request.headers.get("X-Api-Key")).toBe("fixture-api");
    expect(request.headers.get("X-Secret-Key")).toBe("fixture-secret");
    return response;
  });
  const root = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9", retries: 0, fetch: fetchMock as typeof fetch });
  return { scores: root.scores, fetchMock };
}

type Case = [string, (client: ScoresClient) => unknown, string, string, unknown?, Record<string, string>?];
const cases: Case[] = [
  ["list", s => s.list({ source_type: "trace", source_id: "t1", label_id: "l1" }), "GET", "scores/", undefined, { source_type: "trace", source_id: "t1", label_id: "l1" }],
  ["create", s => s.create({ source_type: "trace", source_id: "t1", label_id: "l1", value: { score: 0 } }), "POST", "scores/", { source_type: "trace", source_id: "t1", label_id: "l1", value: { score: 0 } }],
  ["bulk", s => s.bulkCreate({ source_type: "trace", source_id: "t1", scores: [] }), "POST", "scores/bulk/", { source_type: "trace", source_id: "t1", scores: [] }],
  ["get", s => s.get("s1"), "GET", "scores/s1/"],
  ["update", s => s.update("s1", { notes: null }), "PATCH", "scores/s1/", { notes: null }],
  ["delete", s => s.delete("s1"), "DELETE", "scores/s1/"],
  ["source", s => s.forSource("trace", "t1", { project_id: "p1" }), "GET", "scores/for-source/", undefined, { source_type: "trace", source_id: "t1", project_id: "p1" }],
  ["labels list", s => s.labels.list({ type: "star", include_archived: true }), "GET", "annotations-labels/", undefined, { type: "star", include_archived: "true" }],
  ["label create", s => s.labels.create({ name: "quality", type: "star" }), "POST", "annotations-labels/", { name: "quality", type: "star" }],
  ["label get", s => s.labels.get("l1"), "GET", "annotations-labels/l1/"],
  ["label update", s => s.labels.update("l1", { description: null }), "PATCH", "annotations-labels/l1/", { description: null }],
  ["label delete", s => s.labels.delete("l1"), "DELETE", "annotations-labels/l1/"],
  ["label restore", s => s.labels.restore("l1"), "POST", "annotations-labels/l1/restore/", {}],
];

test.each(cases.map(row => [row] as const))("generated score operation %s", async ([_name, call, method, path, body, query = {}]) => {
  const { scores, fetchMock } = setup();
  const expected = _name === "source" ? { status: true, result: { ok: true } } : { ok: true };
  await expect(call(scores)).resolves.toEqual(expected);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const request = fetchMock.mock.calls[0][0];
  expect(request.method).toBe(method);
  const url = new URL(request.url);
  expect(url.pathname).toBe("/model-hub/" + path);
  expect(Object.fromEntries(url.searchParams.entries())).toEqual(query);
  expect(await request.text()).toBe(body === undefined ? "" : JSON.stringify(body));
});

test.each([undefined, [], [{ source_id: "span1", notes: "Needs review" }]].map(notes => [notes] as const))(
  "source scores retain the complete response with span notes %j",
  async notes => {
    const payload = {
      status: true,
      result: [{ id: "s1", value: { score: 0 } }],
      ...(notes === undefined ? {} : { span_notes: notes }),
    };
    const { scores } = setup(new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json" } }));
    await expect(scores.forSource("observation_span", "span1")).resolves.toEqual(payload);
  },
);

test.each(["list", "forSource"] as const)("logical %s errors retain response headers", async operation => {
  const { scores, fetchMock } = setup(new Response(
    JSON.stringify({ status: false, code: "invalid_score", result: "bad score" }),
    { headers: { "Content-Type": "application/json", "x-request-id": "logical-request", "Retry-After": "7" } },
  ));
  const request = operation === "forSource" ? scores.forSource("observation_span", "span1") : scores.list();
  const error = await request.catch((value: unknown) => value);
  expect(error).toBeInstanceOf(BadRequestError);
  expect(error).toMatchObject({ code: "invalid_score", requestId: "logical-request", retryAfter: 7 });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("score validation errors preserve the server code", async () => {
  const { scores } = setup(new Response(JSON.stringify({ code: "invalid_score", detail: "bad score" }), { status: 400, headers: { "Content-Type": "application/json" } }));
  const error = await scores.create({ source_type: "trace", source_id: "t1", label_id: "l1", value: {} }).catch((value: unknown) => value);
  expect(error).toBeInstanceOf(BadRequestError);
  expect(error).toMatchObject({ code: "invalid_score" });
});
