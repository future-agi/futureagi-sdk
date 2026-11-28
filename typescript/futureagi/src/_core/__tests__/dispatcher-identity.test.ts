/**
 * A dispatcher is recognised by what it is, not by what its class is called: a class that carries the name
 * `EnvHttpProxyAgent` or `Agent` is not undici's, and the SDK never constructs a class the caller supplied. The direct
 * agent for a keyed send is built from undici. A `Pool` or `Client` is pinned to one origin and is direct only for it.
 */
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { Agent, Dispatcher, EnvHttpProxyAgent, MockAgent, Pool, Client } from "undici";

import { dispatcherProxies, plainHttpRouting, resetHttpWarnings } from "../http-security";
import { directDispatcher, loopbackInit } from "../loopback";

const KEY = Symbol.for("undici.globalDispatcher.1");
const slot = globalThis as Record<symbol, unknown>;
const REMOTE = "http://plain.example.test:8080/x";
let saved: unknown;
beforeEach(() => { saved = slot[KEY]; resetHttpWarnings(); });
afterEach(() => { if (saved === undefined) delete slot[KEY]; else slot[KEY] = saved; });

interface Built { count: number; instances: object[] }
function forged(name: string): { cls: new (options?: object) => Dispatcher; built: Built } {
  const built: Built = { count: 0, instances: [] };
  const holder = {
    [name]: class extends Dispatcher {
      constructor(_options?: object) { super(); built.count += 1; built.instances.push(this); }
      dispatch(): boolean { return true; }
    },
  };
  return { cls: holder[name] as never, built };
}

describe("a class that only carries undici's name", () => {
  it("is not the environment's proxy agent: a plain-http send through it counts as proxied", () => {
    const { cls } = forged("EnvHttpProxyAgent");
    slot[KEY] = new cls();
    const routing = plainHttpRouting(REMOTE, { fetchSupplied: false });
    expect(routing.callerProxied).toBe(true);
  });

  it("is never constructed to make a direct agent", () => {
    const { cls, built } = forged("EnvHttpProxyAgent");
    slot[KEY] = new cls();
    built.count = 0;
    expect(loopbackInit(REMOTE, true).dispatcher).toBeUndefined();
    expect(directDispatcher(false, false)).toBeUndefined();
    expect(built.count).toBe(0);
  });

  it("named Agent is never constructed for the name localhost", () => {
    const { cls, built } = forged("Agent");
    slot[KEY] = new cls();
    built.count = 0;
    directDispatcher(true, true);
    expect(built.count).toBe(0);
  });
});

describe("undici's own EnvHttpProxyAgent as the global dispatcher", () => {
  it("is the environment: the send is direct and the direct agent is an undici Agent", () => {
    slot[KEY] = new EnvHttpProxyAgent();
    expect(plainHttpRouting(REMOTE, { fetchSupplied: false })).toEqual({ callerProxied: false, proxiesDisabled: true });
    const dispatcher = directDispatcher(false, false);
    expect(dispatcher).toBeInstanceOf(Agent);
    expect(dispatcherProxies(dispatcher, REMOTE, { HTTP_PROXY: "http://127.0.0.1:9" })).toBe(false);
  });
});

describe("a Pool or Client pinned to one origin", () => {
  const proxyOrigin = "http://127.0.0.1:9";
  it("is not direct for a request to another origin", () => {
    expect(dispatcherProxies(new Pool(proxyOrigin), REMOTE, {})).toBe(true);
    expect(dispatcherProxies(new Client(proxyOrigin), REMOTE, {})).toBe(true);
  });
  it("is direct for a request to its own origin", () => {
    expect(dispatcherProxies(new Pool("http://plain.example.test:8080"), REMOTE, {})).toBe(false);
    expect(dispatcherProxies(new Client("http://plain.example.test:8080"), REMOTE, {})).toBe(false);
  });
  it("leaves a mock agent and a plain Agent direct", () => {
    expect(dispatcherProxies(new MockAgent(), REMOTE, {})).toBe(false);
    expect(dispatcherProxies(new Agent(), REMOTE, {})).toBe(false);
  });
});

/** The runtime's own environment-proxy agent, judged in a child process (the runtime builds it from its own copy of undici). */
describe("the runtime's own EnvHttpProxyAgent", () => {
  const probe = (): { kind: string; recognised: boolean; routing: { callerProxied: boolean; proxiesDisabled: boolean }; direct: string } => {
    const tsx = require.resolve("tsx/cli");
    const out = execFileSync(process.execPath, [tsx, join(__dirname, "../__fixtures__/env-proxy-agent-probe.ts")], {
      encoding: "utf8",
      timeout: 60_000,
      env: { ...process.env, NODE_USE_ENV_PROXY: "1", HTTP_PROXY: "http://127.0.0.1:9", NO_PROXY: "" },
    });
    return JSON.parse(out.trim().split("\n").pop() as string);
  };
  it("is not proven when the runtime loads its undici before the SDK: a keyed plain-http send through it counts as a caller's proxy, and no direct agent is built", () => {
    const seen = probe();
    // a runtime that does not read NODE_USE_ENV_PROXY has no such agent to judge
    if (seen.kind !== "EnvHttpProxyAgent") return;
    // NODE_USE_ENV_PROXY loads the runtime's undici at start-up, so the SDK reads no class of that copy and builds none
    // from the agent in the slot; the `undici` package's classes do not match the runtime's agent
    expect(seen.recognised).toBe(false);
    expect(seen.routing).toEqual({ callerProxied: true, proxiesDisabled: false });
    expect(seen.direct).toBe("none");
  }, 90_000);
});
