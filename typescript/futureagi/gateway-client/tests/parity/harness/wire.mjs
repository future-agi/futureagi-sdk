// Scripted fetch for the recorder: every request goes to a script.
//
// Wire.install() replaces globalThis.fetch for one case and refuses sockets
// (net.connect / tls.connect / http(s).request), so nothing reaches a network.
// Replies are the same JSON shapes the Python recorder uses (see _wire.py):
//   {status, headers, json} | {status, headers, sse: [...]} | {status, headers, raw: [...]}
//   {status, headers, text} | {raise: "connect"|"read_timeout"|...}; "drop_after": true
//   errors the body after its chunks.
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
export const UNSCRIPTED = { status: 599, json: { error: { message: "unscripted request" } } };
const encoder = new TextEncoder();

function contentType(reply) {
  if ("sse" in reply) return "text/event-stream";
  if ("json" in reply) return "application/json";
  return "text/plain; charset=utf-8";
}

function bodyChunks(reply) {
  if ("sse" in reply) return reply.sse.map((f) => `data: ${f}\n\n`);
  if ("raw" in reply) return reply.raw;
  if ("json" in reply) return [JSON.stringify(reply.json)];
  if ("text" in reply) return reply.text ? [reply.text] : [];
  return [];
}

function scriptedError(kind) {
  if (kind === "connect") {
    const cause = Object.assign(new Error("connect ECONNREFUSED 127.0.0.1:9"), { code: "ECONNREFUSED" });
    return new TypeError("fetch failed", { cause });
  }
  if (kind === "remote_protocol") return new TypeError("terminated");
  return new DOMException("The operation was aborted due to timeout", "TimeoutError");
}

function headerList(init, input) {
  const out = [];
  const source = init?.headers ?? (input instanceof Request ? input.headers : undefined);
  const h = new Headers();
  if (source instanceof Headers) source.forEach((v, k) => h.append(k, v));
  else if (Array.isArray(source)) for (const [k, v] of source) h.append(k, v);
  else if (source) for (const [k, v] of Object.entries(source)) if (v !== undefined && v !== null) h.append(k, String(v));
  h.forEach((v, k) => out.push([k, k === "content-type" ? v.replace(/boundary=[-\w]+/, "boundary=BOUNDARY") : v]));
  return out.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : 1));
}

async function formParts(form) {
  const parts = [];
  for (const [name, value] of form.entries()) {
    if (typeof value === "string") parts.push({ name, text: value });
    else parts.push({ name, filename: value.name, type: value.type, text: await value.text() });
  }
  return parts;
}

export class Wire {
  constructor(det) {
    this.det = det;
    this.replies = [];
    this.requests = [];
    this._saved = [];
  }

  script(...replies) {
    this.replies.push(...replies);
  }

  async _record(input, init) {
    const url = new URL(typeof input === "string" || input instanceof URL ? String(input) : input.url);
    const entry = {
      method: (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase(),
      scheme: url.protocol.replace(":", ""),
      host: url.hostname,
      port: url.port ? Number(url.port) : null,
      path: url.pathname,
      query: [...url.searchParams.entries()].sort(),
      headers: headerList(init, input),
      timeout_ms: init?.signal ? (this.det.signalTimeouts.get(init.signal) ?? "<signal>") : null,
    };
    const body = init?.body;
    if (body instanceof FormData) entry.multipart = await formParts(body);
    else if (typeof body === "string" && body) {
      try {
        entry.json = JSON.parse(body);
      } catch {
        entry.body = { text: body };
      }
    } else if (body) entry.body = { type: Object.prototype.toString.call(body) };
    this.requests.push(entry);
  }

  async fetch(input, init) {
    await this._record(input, init);
    const reply = this.replies.length ? this.replies.shift() : UNSCRIPTED;
    if (reply.raise) throw scriptedError(reply.raise);
    const chunks = bodyChunks(reply);
    const stream = new ReadableStream({
      start(controller) {
        for (const c of chunks) controller.enqueue(encoder.encode(c));
        if (reply.drop_after) controller.error(new TypeError("terminated"));
        else controller.close();
      },
    });
    const headers = new Headers(reply.headers ?? {});
    if (!headers.has("content-type")) headers.set("content-type", contentType(reply));
    return new Response(chunks.length || reply.drop_after ? stream : null, { status: reply.status ?? 200, headers });
  }

  install() {
    const wire = this;
    const refuse = () => {
      throw new Error("parity recorder: network access is refused");
    };
    const patch = (owner, name, value) => {
      this._saved.push([owner, name, owner[name]]);
      owner[name] = value;
    };
    patch(globalThis, "fetch", (input, init) => wire.fetch(input, init));
    for (const mod of ["node:net", "node:tls", "node:http", "node:https"]) {
      const m = require(mod);
      for (const fn of ["connect", "createConnection", "request", "get"]) if (typeof m[fn] === "function") patch(m, fn, refuse);
    }
  }

  remove() {
    while (this._saved.length) {
      const [owner, name, value] = this._saved.pop();
      owner[name] = value;
    }
  }
}
