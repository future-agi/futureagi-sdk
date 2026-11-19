import { FutureAGIClient } from "../../futureagi-client";
import { FIXTURE_ID, invokePublic, methodAt, publicPath } from "./contract-public";
import { payloads } from "./contract-payloads";
import { retryClassOf } from "../policy";

export type Case = Record<string, any>;
export const pathArgs = (row: Case): Record<string, string> => Object.fromEntries(row.path_params.map((p: string) => [p, String(row.path_values?.[p] ?? FIXTURE_ID)]));
export const streamEvents = (row: Case): string[] => [
  ...row.stream.known_events.filter((event: string) => event !== "done"),
  ...(row.stream.known_events.includes("done") ? ["done"] : []),
];

export function success(row: Case): Response {
  if (row.stream) {
    const body = ": heartbeat\n\n" + streamEvents(row).map((e: string, i: number) =>
      `event: ${e}\nid: ${i + 1}\ndata: {"type":"${e}","marker":"kept"}\n\n`).join("");
    return new Response(body, { headers: { "content-type": "text/event-stream" } });
  }
  const status = row.success_status ?? 200;
  return status === 204 ? new Response(null, { status }) : Response.json(payloads(row).wire, { status });
}

export function runtime(row: Case, handler: (request: Request) => Response, retries = 0) {
  let preparing: Case | undefined;
  const setupRequests: Request[] = [];
  const fetcher = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init);
    if (!preparing) return handler(request);
    setupRequests.push(request);
    expect(request.method).toBe(preparing.request.method);
    expect(request.url).toBe("http://127.0.0.1:9" + preparing.request.path);
    expect(request.headers.has("Idempotency-Key")).toBe(false);
    return Response.json(preparing.response);
  }) as typeof fetch;
  const client = new FutureAGIClient({ apiKey: "contract-api", secretKey: "contract-secret", baseUrl: "http://127.0.0.1:9", fetch: fetcher, retries });
  const core = client._platform;
  Object.assign(core.shared, { sleep: async () => undefined });
  const handles: Record<string, any> = {};
  async function prepare(): Promise<void> {
    const root = publicPath(row).split(".")[0];
    if (root !== "client" && !handles[root]) {
      const fixture = row.handle_fixtures?.[root];
      if (!fixture?.ts) throw new Error(`public handle fixture required for ${root}; no executor fallback`);
      preparing = fixture;
      try {
        const before = setupRequests.length;
        const { owner, method } = methodAt(client, fixture.ts.path);
        handles[root] = await method.apply(owner, fixture.ts.args ?? []);
        expect(setupRequests).toHaveLength(before + 1);
        expect(handles[root].id).toBe(FIXTURE_ID);
      } finally { preparing = undefined; }
    }
  }
  async function call(): Promise<any> {
    await prepare();
    const result = await invokePublic(client, row, handles);
    if (!row.stream) return result;
    const events = [];
    for await (const event of result) events.push(event);
    return events;
  }
  return { call, prepare, core, client, handles, setupRequests };
}

export function checkWire(row: Case, request: Request): void {
  let path = row.path;
  for (const [key, value] of Object.entries(pathArgs(row))) path = path.replace(`{${key}}`, value);
  if (row.adapter === "platform" || row.platform_origin) path = "/omega/api" + path;
  expect(request.method).toBe(row.method);
  expect(new URL(request.url).pathname).toBe(path);
  expect(request.headers.has("Idempotency-Key")).toBe(row.idempotent);
  if (row.adapter === "platform" || row.platform_origin) {
    const subject = runtime(row, () => { throw new Error("policy lookup must not request"); });
    expect(retryClassOf(subject.core.operation(row.name))).toBe(row.retry);
  }
}
