/**
 * D-06b: one metadata rule. A request sends one x-agentcc-metadata JSON
 * header: the client's `metadata`, then the session's, then the request's
 * `request_metadata`, merged key by key, the later layer winning.
 * @agentcc/client 1.0.1 replaced instead: a request's request_metadata
 * dropped the client's metadata, and a client's metadata dropped a session's
 * (the session's header sat under the client's). Raw headers stay raw: an
 * x-agentcc-metadata in extra_headers, in any spelling, is sent as given, and
 * withOptions({ metadata }) sets a new client's metadata.
 *
 * x-agentcc-metadata is one header in every spelling, at every layer: fetch
 * joins two spellings of one name with ", ", which is not JSON, so the
 * "one header" tests below read what fetch sends (new Headers(init.headers))
 * and count the keys in any case, and one test runs on a real node:http
 * server with the global fetch.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { createServer, type IncomingMessage } from "node:http";
import { AgentCC } from "../../src/index.js";
import { mergeMetadata as mergeMetadataForTest } from "../../src/request-parts.js";
import { assignHeaders } from "../../src/metadata-header.js";

function wire(json: unknown = { id: "c", object: "chat.completion", created: 1, model: "m", choices: [] }) {
  const calls: Array<{ url: string; headers: Record<string, string>; body: Record<string, unknown> }> = [];
  const fetch = jest.fn<typeof globalThis.fetch>(async (url, init) => {
    calls.push({
      url: String(url),
      headers: { ...(init?.headers as Record<string, string>) },
      body: (typeof init?.body === "string" ? JSON.parse(init.body) : {}) as Record<string, unknown>,
    });
    return new Response(JSON.stringify(json), { status: 200, headers: { "content-type": "application/json" } });
  });
  return { fetch, calls };
}

const MSG = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };
const sent = (h: Record<string, string>) => (h["x-agentcc-metadata"] === undefined ? undefined : JSON.parse(h["x-agentcc-metadata"]));
/** The metadata header as fetch sends it (spellings joined), and every key that spells it. */
const onWire = (h: Record<string, string>) => ({
  value: new Headers(h).get("x-agentcc-metadata"),
  keys: Object.keys(h).filter((name) => name.toLowerCase() === "x-agentcc-metadata"),
});
const RAW = '{"raw":true}';

/** A real HTTP server on 127.0.0.1: every request's headers as Node parsed them, and the raw name/value list. */
async function realServer() {
  const seen: Array<{ headers: IncomingMessage["headers"]; raw: string[] }> = [];
  const srv = createServer((req, res) => {
    seen.push({ headers: req.headers, raw: req.rawHeaders });
    req.resume();
    req.on("end", () => {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ id: "c", object: "chat.completion", created: 1, model: "m", choices: [] }));
    });
  });
  await new Promise<void>((resolve) => srv.listen(0, "127.0.0.1", () => resolve()));
  const { port } = srv.address() as { port: number };
  return { seen, baseUrl: `http://127.0.0.1:${port}`, close: () => new Promise<void>((resolve) => srv.close(() => resolve())) };
}
const rawMetadata = (raw: string[]) =>
  raw.flatMap((name, i) => (i % 2 === 0 && name.toLowerCase() === "x-agentcc-metadata" ? [raw[i + 1]] : []));

describe("D-06b request metadata: client, then session, then request, key by key", () => {
  it("client metadata alone is sent as before", async () => {
    const { fetch, calls } = wire();
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { team: "a", n: 2 } }).chat.completions.create(MSG);
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(JSON.stringify({ team: "a", n: 2 }));
  });

  it("session metadata alone is sent as before", async () => {
    const { fetch, calls } = wire();
    const { client } = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).session({ metadata: { run: 1 } });
    await client.chat.completions.create(MSG);
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(JSON.stringify({ run: 1 }));
  });

  it("request_metadata alone is sent as before and leaves the body", async () => {
    const { fetch, calls } = wire();
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).chat.completions.create({ ...MSG, request_metadata: { k: "v" } });
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(JSON.stringify({ k: "v" }));
    expect(calls[0].body).not.toHaveProperty("request_metadata");
  });

  it("client + request: both keys are sent, the request's value wins on a shared key", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1, shared: "client" } });
    await client.chat.completions.create({ ...MSG, request_metadata: { b: 2, shared: "request" } });
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(JSON.stringify({ a: 1, shared: "request", b: 2 }));
  });

  it("client + session: the session's value wins on a shared key", async () => {
    const { fetch, calls } = wire();
    const base = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { app: "x", shared: "client" } });
    const { client } = base.session({ sessionId: "s1", metadata: { run: 1, shared: "session" } });
    await client.chat.completions.create(MSG);
    expect(sent(calls[0].headers)).toEqual({ app: "x", shared: "session", run: 1 });
    expect(calls[0].headers["x-agentcc-session-id"]).toBe("s1");
  });

  it("session + request: the request's value wins on a shared key", async () => {
    const { fetch, calls } = wire();
    const { client } = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).session({ metadata: { run: 1, shared: "session" } });
    await client.chat.completions.create({ ...MSG, request_metadata: { step: "plan", shared: "request" } });
    expect(sent(calls[0].headers)).toEqual({ run: 1, shared: "request", step: "plan" });
  });

  it("all three layers: one header, in layer order, the latest layer winning each shared key", async () => {
    const { fetch, calls } = wire();
    const base = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: "client", ab: "client", abc: "client" } });
    const { client } = base.session({ metadata: { b: "session", ab: "session", abc: "session" } });
    await client.chat.completions.create({ ...MSG, request_metadata: { c: "request", abc: "request" } });
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(
      JSON.stringify({ a: "client", ab: "session", abc: "request", b: "session", c: "request" }),
    );
  });

  it("the merge is shallow: a nested object in a later layer replaces the earlier one whole", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { tags: { env: "prod", tier: "gold" } } });
    await client.chat.completions.create({ ...MSG, request_metadata: { tags: { env: "dev" } } });
    expect(sent(calls[0].headers)).toEqual({ tags: { env: "dev" } });
  });

  it("the session layer changes nothing else: id, name and path headers are sent as before", async () => {
    const { fetch, calls } = wire();
    const { client, session } = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } }).session({
      sessionId: "s2",
      name: "agent",
      metadata: { b: 2 },
    });
    await client.chat.completions.create(MSG);
    expect(calls[0].headers).toMatchObject({ "x-agentcc-session-id": "s2", "x-agentcc-session-name": "agent" });
    expect(sent(calls[0].headers)).toEqual({ a: 1, b: 2 });
    expect(JSON.parse(session.toHeaders()["x-agentcc-metadata"])).toEqual({ b: 2 });
  });

  it("the same rule on a stream request, on completions, embeddings and images", async () => {
    const sse = new Response("data: [DONE]\n\n", { status: 200, headers: { "content-type": "text/event-stream" } });
    const { fetch, calls } = wire({ object: "list", data: [] });
    fetch.mockImplementationOnce(async (url, init) => {
      calls.push({ url: String(url), headers: { ...(init?.headers as Record<string, string>) }, body: {} });
      return sse;
    });
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } });
    for await (const _ of await client.chat.completions.create({ ...MSG, stream: true, request_metadata: { b: 2 } })) void _;
    await client.completions.create({ model: "m", prompt: "p", request_metadata: { b: 2 } } as never);
    await client.embeddings.create({ model: "m", input: "x", request_metadata: { b: 2 } } as never);
    await client.images.generate({ model: "m", prompt: "p", request_metadata: { b: 2 } } as never);
    expect(calls.map((c) => [new URL(c.url).pathname, sent(c.headers)])).toEqual([
      ["/v1/chat/completions", { a: 1, b: 2 }],
      ["/v1/completions", { a: 1, b: 2 }],
      ["/v1/embeddings", { a: 1, b: 2 }],
      ["/v1/images/generations", { a: 1, b: 2 }],
    ]);
  });

  it("dryRun and buildRequest show the merged header the wire gets", async () => {
    const { fetch, calls } = wire();
    const { client } = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } }).session({ metadata: { b: 2 } });
    const dry = client.chat.completions.dryRun({ ...MSG, request_metadata: { c: 3 } });
    await client.chat.completions.create({ ...MSG, request_metadata: { c: 3 } });
    expect(dry.headers["x-agentcc-metadata"]).toBe(JSON.stringify({ a: 1, b: 2, c: 3 }));
    expect(calls[0].headers["x-agentcc-metadata"]).toBe(dry.headers["x-agentcc-metadata"]);
    const built = client.buildRequest({ method: "POST", path: "/v1/x", metadata: { c: 4 } });
    expect(built.headers["x-agentcc-metadata"]).toBe(JSON.stringify({ a: 1, b: 2, c: 4 }));
  });

  it("a callback sees the x-agentcc-metadata the wire gets for a request with request_metadata", async () => {
    const { fetch, calls } = wire();
    const seen: Array<string | undefined> = [];
    const spy = { onRequestStart: (req: { headers: Record<string, string> }) => void seen.push(req.headers["x-agentcc-metadata"]) };
    const { client } = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 }, callbacks: [spy as never] }).session({ metadata: { b: 2 } });
    await client.chat.completions.create({ ...MSG, request_metadata: { c: 3 } });
    await client.chat.completions.create(MSG);
    expect(seen).toEqual([calls[0].headers["x-agentcc-metadata"], undefined]);
    expect(seen[0]).toBe(JSON.stringify({ a: 1, b: 2, c: 3 }));
  });

  it("an x-agentcc-metadata in extra_headers is a raw header: sent as given, in place of the merge", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } });
    await client.chat.completions.create({ ...MSG, request_metadata: { b: 2 }, extra_headers: { "x-agentcc-metadata": '{"raw":true}' } });
    expect(calls[0].headers["x-agentcc-metadata"]).toBe('{"raw":true}');
  });

  it("an x-agentcc-metadata in extra_headers, in any spelling, is the one header sent: as given, in place of the merge", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } });
    await client.chat.completions.create({ ...MSG, request_metadata: { c: 3 }, extra_headers: { "X-AgentCC-Metadata": RAW } });
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).chat.completions.create({
      ...MSG,
      request_metadata: { c: 3 },
      extra_headers: { "X-AgentCC-Metadata": RAW },
    });
    const { client: sess } = client.session({ metadata: { b: 2 } });
    await sess.chat.completions.create({ ...MSG, extra_headers: { "X-AGENTCC-METADATA": RAW } });
    await client.completions.create({ model: "m", prompt: "p", request_metadata: { c: 3 }, extra_headers: { "x-AgentCC-metadata": RAW } } as never);
    expect(calls.map((c) => onWire(c.headers))).toEqual(Array(4).fill({ value: RAW, keys: ["x-agentcc-metadata"] }));
  });

  it("on a real HTTP server, a mixed-case raw header in extra_headers arrives once, as given", async () => {
    const server = await realServer();
    try {
      const client = new AgentCC({ apiKey: "k", baseUrl: server.baseUrl, metadata: { a: 1 } });
      await client.chat.completions.create({ ...MSG, request_metadata: { c: 3 }, extra_headers: { "X-AgentCC-Metadata": RAW } });
      await new AgentCC({ apiKey: "k", baseUrl: server.baseUrl }).chat.completions.create({
        ...MSG,
        request_metadata: { c: 3 },
        extra_headers: { "X-AgentCC-Metadata": RAW },
      });
    } finally {
      await server.close();
    }
    expect(server.seen.map((s) => [s.headers["x-agentcc-metadata"], rawMetadata(s.raw)])).toEqual([
      [RAW, [RAW]],
      [RAW, [RAW]],
    ]);
  });

  it("a callback sees the one raw x-agentcc-metadata the wire gets, for any spelling in extra_headers", async () => {
    const { fetch, calls } = wire();
    const seen: Array<Record<string, string>> = [];
    const spy = { onRequestStart: (req: { headers: Record<string, string> }) => void seen.push(req.headers) };
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 }, callbacks: [spy as never] });
    await client.chat.completions.create({ ...MSG, request_metadata: { c: 3 }, extra_headers: { "X-AgentCC-Metadata": RAW } });
    expect(onWire(seen[0])).toEqual({ value: RAW, keys: ["x-agentcc-metadata"] });
    expect(onWire(calls[0].headers)).toEqual(onWire(seen[0]));
  });

  it("files and rerank pass extra_headers as given: any spelling of x-agentcc-metadata replaces the client's metadata", async () => {
    const { fetch, calls } = wire({ object: "list", results: [] });
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } });
    await client.rerank.rank({ model: "m", query: "q", documents: ["d"], extra_headers: { "X-AgentCC-Metadata": RAW } } as never);
    await client.files.create({ file: new Blob(["x"]), purpose: "batch", extra_headers: { "X-Agentcc-Metadata": RAW } } as never);
    expect(calls.map((c) => [new URL(c.url).pathname, onWire(c.headers)])).toEqual([
      ["/v1/rerank", { value: RAW, keys: ["x-agentcc-metadata"] }],
      ["/v1/files", { value: RAW, keys: ["x-agentcc-metadata"] }],
    ]);
  });

  it("a low-level request: any spelling of x-agentcc-metadata in its headers is sent, and seen by callbacks, in place of the merge", async () => {
    const { fetch, calls } = wire();
    const seen: Array<Record<string, string>> = [];
    const spy = { onRequestStart: (req: { headers: Record<string, string> }) => void seen.push(req.headers) };
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 }, callbacks: [spy as never] });
    await client.request({ method: "POST", path: "/v1/x", body: {}, headers: { "X-AgentCC-Metadata": RAW }, metadata: { c: 3 } });
    expect(client.buildRequest({ method: "POST", path: "/v1/x", headers: { "X-AgentCC-Metadata": RAW }, metadata: { c: 3 } }).headers).toMatchObject({
      "x-agentcc-metadata": RAW,
    });
    expect([onWire(calls[0].headers), onWire(seen[0])]).toEqual([
      { value: RAW, keys: ["x-agentcc-metadata"] },
      { value: RAW, keys: ["x-agentcc-metadata"] },
    ]);
  });

  it("a defaultHeaders x-agentcc-metadata in another spelling is one header: alone it is sent, under metadata the merge replaces it", async () => {
    const { fetch, calls } = wire();
    const defaultHeaders = { "X-AgentCC-Metadata": '{"d":1}' };
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultHeaders }).chat.completions.create(MSG);
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultHeaders, metadata: { a: 1 } }).chat.completions.create(MSG);
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, defaultHeaders }).chat.completions.create({ ...MSG, request_metadata: { c: 3 } });
    expect(calls.map((c) => onWire(c.headers))).toEqual([
      { value: '{"d":1}', keys: ["x-agentcc-metadata"] },
      { value: '{"a":1}', keys: ["x-agentcc-metadata"] },
      { value: '{"c":3}', keys: ["x-agentcc-metadata"] },
    ]);
  });

  it("assignHeaders: only x-agentcc-metadata is one header in every spelling; other names merge as Object.assign does", () => {
    const merged = assignHeaders({ Authorization: "Bearer a", "x-agentcc-metadata": "{}" }, { authorization: "Bearer b", "X-AgentCC-Metadata": RAW });
    expect(merged).toEqual({ Authorization: "Bearer a", authorization: "Bearer b", "x-agentcc-metadata": RAW });
    expect(assignHeaders({ a: "1" }, undefined)).toEqual({ a: "1" });
    expect(assignHeaders({ a: "1" }, null)).toEqual({ a: "1" });
  });

  it("withOptions({ metadata }) sets the new client's metadata (it is not a fourth layer)", async () => {
    const { fetch, calls } = wire();
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: { a: 1 } }).withOptions({ metadata: { z: 9 } });
    await client.chat.completions.create({ ...MSG, request_metadata: { b: 2 } });
    expect(sent(calls[0].headers)).toEqual({ z: 9, b: 2 });
  });

  it("no layer set: no metadata header; an empty layer is sent as {}, as before", async () => {
    const { fetch, calls } = wire();
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch }).chat.completions.create(MSG);
    await new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, metadata: {} }).chat.completions.create(MSG);
    expect(calls[0].headers).not.toHaveProperty("x-agentcc-metadata");
    expect(calls[1].headers["x-agentcc-metadata"]).toBe("{}");
  });

  it("mergeMetadata: undefined layers are skipped and later keys win", () => {
    expect(mergeMetadataForTest()).toBeUndefined();
    expect(mergeMetadataForTest(undefined, undefined)).toBeUndefined();
    expect(mergeMetadataForTest({ a: 1, b: 1 }, undefined, { b: 2 })).toEqual({ a: 1, b: 2 });
  });
});
