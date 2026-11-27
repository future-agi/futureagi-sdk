// The agents a caller's adapter function receives.
//
// A caller may hand axios an adapter function (on the client's axios instance, or as the adapter of one request) that
// receives the request config, supplies an agent of its own when the config has none (`config.httpsAgent ??= agent`),
// and passes the config to axios's http adapter. For a request with no proxy on its route, that function receives
// `httpAgent` and `httpsAgent` as the caller set them: the same objects the caller put in the instance defaults or in
// the request config, and undefined when the caller set none. The agent the function supplies is the one the request
// goes through:
//
// - a pinning agent (its own CA, and a checkServerIdentity that compares the certificate fingerprint with a pin) is
//   consulted for the TLS connection; a target whose certificate is outside the pin is refused with "pin mismatch",
//   and no key byte reaches it, while a target inside the pin answers 200;
// - an agent that trusts a private CA (not trusted by this process) reaches a target signed by that CA, keyed or not;
// - an https.Agent subclass with a #private field keeps its identity, so a method that reads that field works when
//   called on `config.httpsAgent`, and the request goes through the subclass's createConnection.
//
// Targets are https listeners on a host name that a lookup shim resolves to the loopback address. Their certificates
// come from a scratch CA made for this file with the openssl command line; that CA is trusted by this process only
// inside the pinning block (and restored after it). No proxy variable applies to the target: either every proxy
// variable is cleared, or NO_PROXY names the target host while HTTP_PROXY and HTTPS_PROXY name a recording proxy.
// Keys are planted markers made per test, and every target counts the marker bytes it receives after TLS.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes, X509Certificate } from "node:crypto";
import * as fs from "node:fs";
import * as https from "node:https";
import * as os from "node:os";
import * as path from "node:path";
import { spawnSync } from "node:child_process";
import * as nodeTls from "node:tls";

import axios from "axios";

import { APIKeyAuth, HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

/** node:tls with the CA functions of Node 22.19+ and 24.5+ (the installed @types/node does not declare them). */
const tls = nodeTls as typeof nodeTls & {
  getCACertificates(kind?: string): string[];
  setDefaultCACertificates(certificates: string[]): void;
};

jest.setTimeout(30_000);

const SHIM: string = fx.SHIM_HOST;
const REPLY_BODY: string = fx.REPLY_BODY;

type ProxySink = { port: number; connections: number; raw(): string; count(markers: string[]): number; close(): Promise<void> };

// --- a scratch CA of this file, with two server certificates ---------------------------------------------------

interface Pki {
  ca: string;
  /** Server certificate whose fingerprint is in the pin. */
  pinned: { key: string; cert: string; fingerprint: string };
  /** Server certificate from the same CA whose fingerprint is outside the pin. */
  other: { key: string; cert: string; fingerprint: string };
}

function makePki(): Pki {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-adapter-agent-"));
  try {
    const run = (args: string[]) => {
      const out = spawnSync("openssl", args, { cwd: dir, encoding: "utf8" });
      if (out.status !== 0) throw new Error(`openssl ${args[0]} failed: ${out.stderr}`);
    };
    fs.writeFileSync(path.join(dir, "ext.cnf"), `subjectAltName=DNS:${SHIM},DNS:localhost,IP:127.0.0.1\nbasicConstraints=CA:FALSE\n`);
    run(["req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "2", "-subj", "/CN=fi-adapter-agent-ca"]);
    const leaf = (name: string) => {
      run(["req", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", `${name}.key`, "-out", `${name}.csr`, "-subj", `/CN=${SHIM}`]);
      run(["x509", "-req", "-in", `${name}.csr`, "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out", `${name}.pem`, "-days", "2", "-extfile", "ext.cnf"]);
      const cert = fs.readFileSync(path.join(dir, `${name}.pem`), "utf8");
      return { key: fs.readFileSync(path.join(dir, `${name}.key`), "utf8"), cert, fingerprint: new X509Certificate(cert).fingerprint256 };
    };
    const pinned = leaf("pinned");
    const other = leaf("other");
    return { ca: fs.readFileSync(path.join(dir, "ca.pem"), "utf8"), pinned, other };
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

let pki: Pki;
let undoShim: () => void = () => undefined;
beforeAll(() => {
  pki = makePki();
  undoShim = fx.shimLookup();
});
afterAll(() => {
  undoShim();
});

// --- listeners, agents and clients, closed after each test ----------------------------------------------------

interface Target {
  port: number;
  connections: number;
  requests: string[];
  count(markers: string[]): number;
  close(): Promise<void>;
}

const open: Array<{ close(): Promise<void> }> = [];
const agents: https.Agent[] = [];
const clients: HttpClient[] = [];
afterEach(async () => {
  while (clients.length) {
    const made = clients.pop()!;
    let timer: NodeJS.Timeout | undefined;
    await Promise.race([made.close(), new Promise((resolve) => (timer = setTimeout(resolve, 2000)))]);
    clearTimeout(timer);
  }
  while (agents.length) agents.pop()!.destroy();
  while (open.length) await open.pop()!.close();
});

/** An https listener on 127.0.0.1 with the given certificate; it records the bytes it receives after TLS and answers
 * each request with 200 and a JSON body on its own connection. */
async function tlsTarget(identity: { key: string; cert: string }): Promise<Target> {
  const chunks: string[] = [];
  const requests: string[] = [];
  const sockets = new Set<nodeTls.TLSSocket>();
  const state = { connections: 0 };
  const server = nodeTls.createServer({ key: identity.key, cert: identity.cert }, (socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    let answered = false;
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (answered) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      answered = true;
      requests.push(head);
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  server.on("tlsClientError", () => undefined);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const made: Target = {
    port: (server.address() as { port: number }).port,
    get connections() {
      return state.connections;
    },
    requests,
    count: (markers) => {
      const all = chunks.join("");
      let bytes = 0;
      for (const mark of markers) {
        for (let at = all.indexOf(mark); at >= 0; at = all.indexOf(mark, at + mark.length)) bytes += mark.length;
      }
      return bytes;
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  open.push(made);
  return made;
}

async function proxySink(): Promise<ProxySink> {
  const made: ProxySink = await fx.proxySink();
  open.push(made);
  return made;
}

function keep<A extends https.Agent>(agent: A): A {
  agents.push(agent);
  return agent;
}

// --- environment ----------------------------------------------------------------------------------------------

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

/** Run `run` with every variable of ENV_NAMES cleared and then `set` applied; restore the environment afterwards. */
async function withEnv<T>(set: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, set);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

/** How the environment keeps a proxy variable from applying to the target. `other` is a recording proxy. */
interface Env {
  name: string;
  vars(other: ProxySink): Record<string, string>;
}

const ENVS: Env[] = [
  { name: "every proxy variable cleared", vars: () => ({}) },
  {
    name: "NO_PROXY naming the target host, HTTP_PROXY and HTTPS_PROXY naming a recording proxy",
    vars: (other) => ({ HTTP_PROXY: `http://127.0.0.1:${other.port}`, HTTPS_PROXY: `http://127.0.0.1:${other.port}`, NO_PROXY: SHIM }),
  },
];

// --- where the caller puts the adapter function ---------------------------------------------------------------

/** Where the caller puts the adapter function, and how the GET is made. `extra` is added to the request config. */
interface Placement {
  name: string;
  get(client: HttpClient, adapter: (config: any) => Promise<any>, extra?: Record<string, unknown>): Promise<any>;
}

const PLACEMENTS: Placement[] = [
  {
    name: "the adapter of the client's axios instance",
    get: (client, adapter, extra) => {
      (client as any)._axiosInstance.defaults.adapter = adapter;
      return extra === undefined
        ? client.request({ method: "GET", url: "/v1/probe" } as any)
        : (client as any)._axiosInstance.request({ method: "GET", url: "/v1/probe", ...extra });
    },
  },
  {
    name: "the adapter of one request (the client's axios instance)",
    get: (client, adapter, extra) => (client as any)._axiosInstance.request({ method: "GET", url: "/v1/probe", ...extra, adapter }),
  },
];

/** An adapter function that supplies `agent` when the config has no https agent and hands the config to axios's http
 * adapter. `seen` receives the agents the function was given. */
function filling(agent: https.Agent, seen: { httpAgent?: unknown; httpsAgent?: unknown; calls: number } = { calls: 0 }): (config: any) => Promise<any> {
  const httpAdapter = (axios as any).getAdapter("http");
  return (config: any) => {
    seen.calls++;
    seen.httpAgent = config.httpAgent;
    seen.httpsAgent = config.httpsAgent;
    config.httpsAgent ??= agent;
    return httpAdapter(config);
  };
}

// --- helpers --------------------------------------------------------------------------------------------------

const marker = (tag: string) => `FIMARK-agent-${tag}-${randomBytes(8).toString("hex")}`;

function unkeyedClient(baseUrl: string): HttpClient {
  const made = new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000 });
  clients.push(made);
  return made;
}

function keyedClient(baseUrl: string, apiKey: string, secretKey: string): HttpClient {
  const made = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl, retryAttempts: 1, timeout: 5000 });
  clients.push(made);
  return made;
}

/** "status <n>" for a response, or "error" with the codes and messages of what the request rejected with and of its
 * causes. */
async function outcome(run: () => Promise<any>): Promise<string> {
  return run().then(
    (response) => `status ${response?.status}`,
    (error) => {
      const parts: string[] = [];
      const seen = new Set<unknown>();
      for (let current = error; current && typeof current === "object" && !seen.has(current); current = current.cause) {
        seen.add(current);
        if (current.code !== undefined) parts.push(String(current.code));
        if (current.message) parts.push(String(current.message));
      }
      return `error ${parts.join(" | ") || String(error)}`;
    },
  );
}

function record(label: string, data: Record<string, unknown>): void {
  // eslint-disable-next-line no-console
  console.log(`${label}: ${JSON.stringify(data)}`);
}

// --- a pinning agent supplied by the adapter function ---------------------------------------------------------

const PIN_CASES = PLACEMENTS.flatMap((placement) => ENVS.map((env) => [placement.name, env.name, { placement, env }] as const));

describe("APIKeyAuth with an adapter function that supplies a pinning agent, with no proxy on the route", () => {
  // Inside this block the scratch CA is trusted by this process as well, so the pin is what tells the two targets apart.
  let caBefore: string[];
  beforeAll(() => {
    caBefore = tls.getCACertificates("default");
    tls.setDefaultCACertificates([...caBefore, pki.ca]);
  });
  afterAll(() => {
    tls.setDefaultCACertificates(caBefore);
  });

  test.each(PIN_CASES)(
    "adapter function on %s, %s: a target outside the pin is refused with pin mismatch and receives no key byte, a target inside the pin answers 200",
    async (_placementName, _envName, { placement, env }) => {
      const inside = await tlsTarget(pki.pinned);
      const outside = await tlsTarget(pki.other);
      const other = await proxySink();
      const checks = { count: 0 };
      const pinningAgent = () =>
        keep(
          new https.Agent({
            ca: pki.ca,
            checkServerIdentity: (host: string, cert: nodeTls.PeerCertificate) => {
              checks.count++;
              const named = nodeTls.checkServerIdentity(host, cert);
              if (named) return named;
              return cert.fingerprint256 === pki.pinned.fingerprint ? undefined : new Error(`pin mismatch for ${host}`);
            },
          }),
        );
      const [apiKey, secretKey] = [marker("pa"), marker("ps")];

      const outsideResult = await withEnv(env.vars(other), () =>
        outcome(() => placement.get(keyedClient(`https://${SHIM}:${outside.port}`, apiKey, secretKey), filling(pinningAgent()))),
      );
      const outsideChecks = checks.count;
      checks.count = 0;
      const insideResult = await withEnv(env.vars(other), () =>
        outcome(() => placement.get(keyedClient(`https://${SHIM}:${inside.port}`, apiKey, secretKey), filling(pinningAgent()))),
      );
      const seen = {
        outsidePinMismatch: outsideResult.includes("pin mismatch"),
        outsideChecked: outsideChecks >= 1,
        outsideKeyBytes: outside.count([apiKey, secretKey]),
        outsideRequests: outside.requests.length,
        insideResult,
        insideChecked: checks.count >= 1,
        insideKeyReceived: inside.count([apiKey]) > 0 && inside.count([secretKey]) > 0,
        otherProxyConnections: other.connections,
      };
      record(`pinning agent, ${placement.name}, ${env.name}`, { ...seen, outsideResult, outsideChecks, insideChecks: checks.count });
      expect(seen).toEqual({
        outsidePinMismatch: true,
        outsideChecked: true,
        outsideKeyBytes: 0,
        outsideRequests: 0,
        insideResult: "status 200",
        insideChecked: true,
        insideKeyReceived: true,
        otherProxyConnections: 0,
      });
    },
  );
});

// --- an agent for a private CA supplied by the adapter function -----------------------------------------------

/** What a request to `port` with the default trust of this process gives (agent: false, no proxy). */
function defaultTrust(port: number): Promise<string> {
  return new Promise((resolve) => {
    const request = https.get({ host: "127.0.0.1", servername: "localhost", port, path: "/", agent: false }, (response) => {
      response.resume();
      resolve(`status ${response.statusCode}`);
    });
    request.on("error", (error: NodeJS.ErrnoException) => resolve(`error ${error.code ?? error.message}`));
  });
}

describe.each(PLACEMENTS.map((placement) => [placement.name, placement] as const))(
  "an adapter function set as %s that supplies an agent trusting a private CA",
  (_name, placement) => {
    test("APIKeyAuth: the keyed request goes through that agent and answers 200, and the key reaches the target", async () => {
      const target = await tlsTarget(pki.pinned);
      const [apiKey, secretKey] = [marker("ca"), marker("cs")];
      const trust = await defaultTrust(target.port);
      const client = keyedClient(`https://${SHIM}:${target.port}`, apiKey, secretKey);
      const result = await withEnv({}, () => outcome(() => placement.get(client, filling(keep(new https.Agent({ ca: pki.ca }))))));
      const seen = {
        trust,
        result,
        keyReceived: target.count([apiKey]) > 0 && target.count([secretKey]) > 0,
      };
      record(`private CA keyed, ${placement.name}`, seen);
      expect(seen).toEqual({ trust: "error UNABLE_TO_VERIFY_LEAF_SIGNATURE", result: "status 200", keyReceived: true });
    });

    test("HttpClient without a key: the request goes through that agent and answers 200", async () => {
      const target = await tlsTarget(pki.pinned);
      const trust = await defaultTrust(target.port);
      const client = unkeyedClient(`https://${SHIM}:${target.port}`);
      const result = await withEnv({}, () => outcome(() => placement.get(client, filling(keep(new https.Agent({ ca: pki.ca }))))));
      const seen = { trust, result, requests: target.requests.length };
      record(`private CA unkeyed, ${placement.name}`, seen);
      expect(seen).toEqual({ trust: "error UNABLE_TO_VERIFY_LEAF_SIGNATURE", result: "status 200", requests: 1 });
    });
  },
);

// --- the agents the adapter function receives -----------------------------------------------------------------

/** An https.Agent with a #private field: `made()` reads it, and `createConnection` counts the connections it makes. */
class CountingAgent extends https.Agent {
  #made = 0;

  made(): number {
    return this.#made;
  }

  createConnection(options: any, callback?: any): any {
    this.#made++;
    return (https.Agent.prototype as any).createConnection.call(this, options, callback);
  }
}

/** Where the caller sets its https agent. */
interface AgentSite {
  name: string;
  /** The request config to add, after setting `agent` where this site puts it. */
  place(client: HttpClient, agent: https.Agent): Record<string, unknown>;
}

const SITES: AgentSite[] = [
  {
    name: "the defaults of the client's axios instance",
    place: (client, agent) => {
      (client as any)._axiosInstance.defaults.httpsAgent = agent;
      return {};
    },
  },
  { name: "the request config", place: (_client, agent) => ({ httpsAgent: agent }) },
];

const IDENTITY_CASES = PLACEMENTS.flatMap((placement) =>
  SITES.flatMap((site) => [false, true].map((keyed) => [placement.name, site.name, keyed ? "APIKeyAuth" : "HttpClient without a key", { placement, site, keyed }] as const)),
);

describe("the https agent the caller set, as an adapter function receives it", () => {
  test.each(IDENTITY_CASES)(
    "adapter function on %s, agent in %s, %s: the function receives that agent object, a #private method on it works, and the request goes through its createConnection with 200",
    async (_placementName, _siteName, _kind, { placement, site, keyed }) => {
      const target = await tlsTarget(pki.pinned);
      const [apiKey, secretKey] = [marker("ia"), marker("is")];
      const base = `https://${SHIM}:${target.port}`;
      const client = keyed ? keyedClient(base, apiKey, secretKey) : unkeyedClient(base);
      const mine = keep(new CountingAgent({ ca: pki.ca }));
      const extra = site.place(client, mine);
      const fallback = keep(new https.Agent({ ca: pki.ca }));
      const httpAdapter = (axios as any).getAdapter("http");
      const inside: { calls: number; same?: boolean; httpAgent?: string; privateRead?: string } = { calls: 0 };
      const adapter = (config: any) => {
        inside.calls++;
        inside.same = config.httpsAgent === mine;
        inside.httpAgent = typeof config.httpAgent;
        try {
          inside.privateRead = `made ${config.httpsAgent.made()}`;
        } catch (error) {
          inside.privateRead = `${(error as Error).name}: ${(error as Error).message}`;
        }
        config.httpsAgent ??= fallback;
        return httpAdapter(config);
      };
      const result = await withEnv({}, () => outcome(() => placement.get(client, adapter, extra)));
      const seen = {
        result,
        calls: inside.calls,
        same: inside.same,
        httpAgent: inside.httpAgent,
        privateRead: inside.privateRead,
        connectionsMade: mine.made(),
        keyReceived: keyed ? target.count([apiKey]) > 0 && target.count([secretKey]) > 0 : null,
      };
      record(`identity, ${placement.name}, ${site.name}, keyed ${keyed}`, seen);
      expect(seen).toEqual({
        result: "status 200",
        calls: 1,
        same: true,
        httpAgent: "undefined",
        privateRead: "made 0",
        connectionsMade: 1,
        keyReceived: keyed ? true : null,
      });
    },
  );

  test.each(PLACEMENTS.flatMap((placement) => [false, true].map((keyed) => [placement.name, keyed ? "APIKeyAuth" : "HttpClient without a key", { placement, keyed }] as const)))(
    "adapter function on %s, %s, no agent set by the caller: the function receives httpAgent and httpsAgent undefined, and the agent it supplies carries the request with 200",
    async (_placementName, _kind, { placement, keyed }) => {
      const target = await tlsTarget(pki.pinned);
      const [apiKey, secretKey] = [marker("na"), marker("ns")];
      const base = `https://${SHIM}:${target.port}`;
      const client = keyed ? keyedClient(base, apiKey, secretKey) : unkeyedClient(base);
      const supplied = keep(new CountingAgent({ ca: pki.ca }));
      const given: { httpAgent?: unknown; httpsAgent?: unknown; calls: number } = { calls: 0 };
      const result = await withEnv({}, () => outcome(() => placement.get(client, filling(supplied, given))));
      const seen = {
        result,
        calls: given.calls,
        httpAgent: typeof given.httpAgent,
        httpsAgent: typeof given.httpsAgent,
        connectionsMade: supplied.made(),
      };
      record(`no agent, ${placement.name}, keyed ${keyed}`, seen);
      expect(seen).toEqual({ result: "status 200", calls: 1, httpAgent: "undefined", httpsAgent: "undefined", connectionsMade: 1 });
    },
  );
});
