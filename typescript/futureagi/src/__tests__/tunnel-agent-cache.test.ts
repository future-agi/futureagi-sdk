// The tunnel agents the SDK keeps for keyed https requests sent through a CONNECT proxy.
//
// One tunnel agent serves one proxy, one Proxy-Authorization value for the CONNECT, one kind of target and one set of
// TLS settings, and keeps its connections alive. A caller that sends each request with a Proxy-Authorization value of
// its own gets a new agent per value; the SDK keeps at most 16 of them, and an agent it lets go closes its idle
// connections and closes each connection in use once the request on it has ended.
//
// The target is an https listener with keep-alive (scratch CA trusted by this process) reached through a host name
// that a lookup shim resolves to the loopback address; HTTPS_PROXY names a loopback relay that counts the client
// connections it holds open and hands every byte to a CONNECT-aware proxy sink. Each case sends keyed requests, each
// with its own planted Proxy-Authorization marker value, then counts the connections that stay open at the relay and
// at the target once the responses are in.

/* eslint-disable @typescript-eslint/no-explicit-any */
import * as https from "node:https";
import * as net from "node:net";

import { APIKeyAuth } from "../api/auth";
import { Client } from "../platform/client";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM_HOST: string = fx.SHIM_HOST;
const REPLY_BODY: string = fx.REPLY_BODY;

/** The most tunnel agents the SDK keeps in one cache (each holds at most one idle connection in these cases). */
const AGENT_LIMIT = 16;

const ENV_NAMES = [
  "HTTP_PROXY",
  "http_proxy",
  "HTTPS_PROXY",
  "https_proxy",
  "ALL_PROXY",
  "all_proxy",
  "NO_PROXY",
  "no_proxy",
  "npm_config_https_proxy",
  "npm_config_http_proxy",
  "npm_config_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
];

/** Run `run` with every variable of ENV_NAMES cleared except `vars`, then restore the environment. */
async function withEnv<T>(vars: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, vars);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

interface Sink {
  port: number;
  connects: string[];
  absolute: string[];
  close(): Promise<void>;
}

/** An https listener with keep-alive that answers 200 with a JSON body. With `hold`, no request is answered before
 * `hold` request heads have arrived (then all of them are answered). */
interface KeepAliveTarget {
  port: number;
  heads: string[];
  /** Connections accepted so far. */
  accepted: number;
  /** Connections open at this moment. */
  open: number;
  close(): Promise<void>;
}

/** A relay in front of the proxy sink: each client connection is piped to the sink on a connection of its own, and
 * the two close together. */
interface Relay {
  port: number;
  /** Client connections accepted so far. */
  accepted: number;
  /** Client connections open at this moment. */
  open: number;
  close(): Promise<void>;
}

const opened: Array<{ close(): Promise<void> }> = [];

let undoLookup: () => void;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});
afterEach(async () => {
  while (opened.length > 0) await opened.pop()!.close();
});

async function keepAliveTarget(hold = 0): Promise<KeepAliveTarget> {
  const { key, cert } = fx.certificates();
  const heads: string[] = [];
  const sockets = new Set<net.Socket>();
  const waiting: Array<() => void> = [];
  const state = { accepted: 0 };
  const server = https.createServer({ key, cert, keepAlive: true, keepAliveTimeout: 60_000 }, (request, response) => {
    const lines = [`${request.method} ${request.url} HTTP/${request.httpVersion}`];
    for (let at = 0; at < request.rawHeaders.length; at += 2) lines.push(`${request.rawHeaders[at]}: ${request.rawHeaders[at + 1]}`);
    heads.push(`${lines.join("\r\n")}\r\n\r\n`);
    const answer = () => {
      response.writeHead(200, { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(REPLY_BODY)) });
      response.end(REPLY_BODY);
    };
    request.resume();
    if (hold <= 0) {
      answer();
      return;
    }
    waiting.push(answer);
    if (heads.length >= hold) {
      for (const release of waiting.splice(0)) release();
    }
  });
  server.on("connection", (socket: net.Socket) => {
    state.accepted++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
  });
  server.on("tlsClientError", () => undefined);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: KeepAliveTarget = {
    port: (server.address() as net.AddressInfo).port,
    heads,
    get accepted() {
      return state.accepted;
    },
    get open() {
      return sockets.size;
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  opened.push(made);
  return made;
}

async function sink(): Promise<Sink> {
  const made: Sink = await fx.proxySink();
  opened.push(made);
  return made;
}

async function relay(toPort: number): Promise<Relay> {
  const clients = new Set<net.Socket>();
  const upstreams = new Set<net.Socket>();
  const state = { accepted: 0 };
  const server = net.createServer((client) => {
    state.accepted++;
    clients.add(client);
    const upstream = net.connect(toPort, "127.0.0.1");
    upstreams.add(upstream);
    client.on("error", () => undefined);
    upstream.on("error", () => undefined);
    client.pipe(upstream);
    upstream.pipe(client);
    client.on("close", () => {
      clients.delete(client);
      upstream.destroy();
    });
    upstream.on("close", () => {
      upstreams.delete(upstream);
      client.destroy();
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: Relay = {
    port: (server.address() as net.AddressInfo).port,
    get accepted() {
      return state.accepted;
    },
    get open() {
      return clients.size;
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of [...clients, ...upstreams]) socket.destroy();
        server.close(() => resolve());
      }),
  };
  opened.push(made);
  return made;
}

/** A proxy route for one case: HTTPS_PROXY names the relay, which hands every byte to the proxy sink. */
async function proxyRoute(): Promise<{ sink: Sink; relay: Relay; url: string }> {
  const proxy = await sink();
  const front = await relay(proxy.port);
  return { sink: proxy, relay: front, url: `http://${SHIM_HOST}:${front.port}` };
}

/** Wait for close events to arrive: return `read()` once it is at most `limit`, or after `waitMs`. */
async function settle(read: () => number, limit: number, waitMs = 1500): Promise<number> {
  for (let waited = 0; read() > limit && waited < waitMs; waited += 20) {
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  await new Promise((resolve) => setTimeout(resolve, 50));
  return read();
}

/** Every value of a header in a request head (lower-case name). */
function headerValues(head: string, name: string): string[] {
  const values: string[] = [];
  for (const line of head.split("\r\n\r\n")[0].split("\r\n").slice(1)) {
    const at = line.indexOf(":");
    if (at > 0 && line.slice(0, at).trim().toLowerCase() === name) values.push(line.slice(at + 1).trim());
  }
  return values;
}

/** Planted Proxy-Authorization values of the caller, one per request. */
const callerValues = (tag: string, count: number) => Array.from({ length: count }, (_, n) => `Basic FIMARK-tac-${tag}-${n}`);

const PAIR = { apiKey: "FIMARK-tac-ak", secretKey: "FIMARK-tac-sk" };

type Sender = "APIKeyAuth" | "the platform Client";
const SENDERS: Sender[] = ["APIKeyAuth", "the platform Client"];

/** A sender of keyed GETs to `baseUrl` + /v1/probe/, each with the Proxy-Authorization value given; each GET settles
 * to its status or to its error text. */
function makeSender(sender: Sender, baseUrl: string): { get(proxyAuthorization: string): Promise<number | string>; close(): Promise<void> } {
  const failed = (error: any) => {
    const e = error as { code?: string; message?: string };
    return `error ${String(e.code ?? "")} ${String(e.message ?? error)}`.trim();
  };
  if (sender === "APIKeyAuth") {
    const client = new APIKeyAuth({ fiApiKey: PAIR.apiKey, fiSecretKey: PAIR.secretKey, baseUrl, retryAttempts: 1, timeout: 10_000, maxWorkers: 64 } as any);
    return {
      get: async (proxyAuthorization) => {
        try {
          const response: any = await client.request({ method: "GET", url: "/v1/probe/", headers: { "Proxy-Authorization": proxyAuthorization } } as any);
          return response.status;
        } catch (error) {
          return failed(error);
        }
      },
      close: () => client.close(),
    };
  }
  const client = new Client({ apiKey: PAIR.apiKey, secretKey: PAIR.secretKey, baseUrl, maxRetries: 0, timeout: 10_000 });
  return {
    get: async (proxyAuthorization) => {
      try {
        await client.request("GET", "/v1/probe/", { unwrap: null }, { headers: { "Proxy-Authorization": proxyAuthorization } });
        return 200;
      } catch (error) {
        return failed(error);
      }
    },
    close: async () => undefined,
  };
}

describe("tunnel agents for keyed https requests whose callers set many distinct Proxy-Authorization values", () => {
  test.each(SENDERS)(
    "%s: 60 sequential requests, each with its own value, all succeed and leave at most 16 tunnel connections open at the proxy and at the target",
    async (sender) => {
      const target = await keepAliveTarget();
      const route = await proxyRoute();
      const values = callerValues(`seq-${sender === "APIKeyAuth" ? "a" : "p"}`, 60);
      const statuses = await withEnv({ HTTPS_PROXY: route.url }, async () => {
        const client = makeSender(sender, `https://${SHIM_HOST}:${target.port}`);
        const out: Array<number | string> = [];
        try {
          for (const value of values) out.push(await client.get(value));
        } finally {
          await client.close();
        }
        return out;
      });
      const openAtProxy = await settle(() => route.relay.open, AGENT_LIMIT);
      const openAtTarget = await settle(() => target.open, AGENT_LIMIT);
      expect({
        failed: statuses.filter((status) => status !== 200),
        succeeded: statuses.filter((status) => status === 200).length,
        targetRequests: target.heads.length,
        connects: route.sink.connects.length,
        connectValues: route.sink.connects.map((head) => headerValues(head, "proxy-authorization").join("\n")),
        absolute: route.sink.absolute.length,
        targetProxyAuthorizationLines: target.heads.flatMap((head) => headerValues(head, "proxy-authorization")).length,
      }).toEqual({
        failed: [],
        succeeded: 60,
        targetRequests: 60,
        connects: 60,
        connectValues: values,
        absolute: 0,
        targetProxyAuthorizationLines: 0,
      });
      expect(route.relay.accepted).toBe(60);
      expect(openAtProxy).toBeLessThanOrEqual(AGENT_LIMIT);
      expect(openAtTarget).toBeLessThanOrEqual(AGENT_LIMIT);
    },
  );

  test.each(SENDERS)(
    "%s: 40 requests with distinct values in flight at the same time all complete, and at most 16 tunnel connections stay open once they have",
    async (sender) => {
      const count = 40;
      // The target answers none of them before all 40 have arrived, so every agent is created while its request is open.
      const target = await keepAliveTarget(count);
      const route = await proxyRoute();
      const values = callerValues(`par-${sender === "APIKeyAuth" ? "a" : "p"}`, count);
      const statuses = await withEnv({ HTTPS_PROXY: route.url }, async () => {
        const client = makeSender(sender, `https://${SHIM_HOST}:${target.port}`);
        try {
          return await Promise.all(values.map((value) => client.get(value)));
        } finally {
          await client.close();
        }
      });
      const openAtProxy = await settle(() => route.relay.open, AGENT_LIMIT);
      const openAtTarget = await settle(() => target.open, AGENT_LIMIT);
      expect({
        failed: statuses.filter((status) => status !== 200),
        succeeded: statuses.filter((status) => status === 200).length,
        targetRequests: target.heads.length,
        targetConnections: target.accepted,
        connectValues: [...route.sink.connects.map((head) => headerValues(head, "proxy-authorization").join("\n"))].sort(),
        absolute: route.sink.absolute.length,
      }).toEqual({
        failed: [],
        succeeded: count,
        targetRequests: count,
        targetConnections: count,
        connectValues: [...values].sort(),
        absolute: 0,
      });
      expect(openAtProxy).toBeLessThanOrEqual(AGENT_LIMIT);
      expect(openAtTarget).toBeLessThanOrEqual(AGENT_LIMIT);
    },
  );

  test("APIKeyAuth: a value sent again after 16 others opens a new tunnel, and a value among the 16 most recent reuses its open tunnel", async () => {
    const target = await keepAliveTarget();
    const route = await proxyRoute();
    const values = callerValues("reuse", 18);
    const statuses = await withEnv({ HTTPS_PROXY: route.url }, async () => {
      const client = makeSender("APIKeyAuth", `https://${SHIM_HOST}:${target.port}`);
      const out: Array<number | string> = [];
      try {
        for (const value of values) out.push(await client.get(value));
        // values[17] is the most recent one: its agent and its idle connection are kept.
        out.push(await client.get(values[17]));
        // values[0] was let go when the 17th agent was made: its request opens a new tunnel.
        out.push(await client.get(values[0]));
      } finally {
        await client.close();
      }
      return out;
    });
    const openAtProxy = await settle(() => route.relay.open, AGENT_LIMIT);
    expect({
      failed: statuses.filter((status) => status !== 200),
      targetRequests: target.heads.length,
      connectValues: route.sink.connects.map((head) => headerValues(head, "proxy-authorization").join("\n")),
    }).toEqual({
      failed: [],
      targetRequests: 20,
      connectValues: [...values, values[0]],
    });
    expect(openAtProxy).toBeLessThanOrEqual(AGENT_LIMIT);
  });
});
