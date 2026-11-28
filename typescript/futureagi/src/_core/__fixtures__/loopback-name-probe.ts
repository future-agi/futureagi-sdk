/**
 * Test fixture (not shipped API): run as its own process by loopback-name-dial.test.ts with the runtime's
 * environment-proxy switch on (`NODE_USE_ENV_PROXY=1`) and `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` naming a listener that
 * records the first request line. A resolver shim answers `localhost` with 127.0.0.2 (a listener of its own on the
 * same port) and `loop.test` with 127.0.0.1. `PROBE_SENDER` picks the sender and `PROBE_CASE` the address written:
 * `localhost-http`, `localhost-https`, `name-https` (`loop.test`), `literal-http` (`127.0.0.1`) or `ipv6-http` (`[::1]`). It prints what every
 * listener saw, the addresses the process connected to and the names it asked the resolver about, as one JSON line.
 *
 * The SDK's dispatcher module loads first, before `node:http` (an ES module graph that imports it loads the runtime's
 * undici while the graph is linked), so it reads the classes of the agent the runtime makes for it, as in a CommonJS
 * application that loads the SDK before its first request. With the switch on, the runtime loads its undici at
 * start-up, and the SDK can prove no agent of that copy; the application then puts the `undici` package's
 * `EnvHttpProxyAgent` in the global slot with the package's `setGlobalDispatcher`, an agent that reads the same proxy
 * variables and that the package's classes prove.
 */

/** The modules the probe uses, loaded in the order the header gives. */
async function load() {
  await import("../dispatcher-provenance");
  if (process.env.NODE_USE_ENV_PROXY === "1") {
    const undici = await import("undici");
    undici.setGlobalDispatcher(new undici.EnvHttpProxyAgent());
  }
  await import("node:http");
  const { APIKeyAuth } = await import("../../api/auth");
  const { HttpMethod } = await import("../../api/types");
  const { Client } = await import("../../platform/client");
  const { installNameShim } = await import("./name-shim");
  const { MARKER_KEY, MARKER_SECRET, Sink } = await import("./plaintext-sinks");
  return { APIKeyAuth, HttpMethod, Client, installNameShim, MARKER_KEY, MARKER_SECRET, Sink };
}
type Loaded = Awaited<ReturnType<typeof load>>;

function senders(m: Loaded): Record<string, (base: string) => PromiseLike<unknown>> {
  const KEYS = { apiKey: m.MARKER_KEY, secretKey: m.MARKER_SECRET };
  const legacy = (base: string) => ({ fiApiKey: m.MARKER_KEY, fiSecretKey: m.MARKER_SECRET, fiBaseUrl: base, retryAttempts: 1 }) as unknown as ConstructorParameters<Loaded["APIKeyAuth"]>[0];
  return {
    "platform Client": (b) => new m.Client({ ...KEYS, baseUrl: b, maxRetries: 0, timeout: 3000 }).request("GET", "/probe"),
    "APIKeyAuth (axios)": (b) => new m.APIKeyAuth(legacy(b)).request({ method: m.HttpMethod.GET, url: "/probe" }),
  };
}

async function main(): Promise<void> {
  const m = await load();
  const { Sink, installNameShim } = m;
  const sender = process.env.PROBE_SENDER ?? "";
  const kind = process.env.PROBE_CASE ?? "";
  const proxy = new Sink("502 Bad Gateway");
  await proxy.listen("127.0.0.1", Number(process.env.PROBE_PROXY_PORT));
  const target = new Sink();
  const answered = new Sink();
  await target.listen(kind === "ipv6-http" ? "::1" : "127.0.0.1");
  const port = target.port;
  await answered.listen("127.0.0.2", port);
  if (kind.endsWith("https")) { target.mode = "tls"; answered.mode = "tls"; }
  const shim = installNameShim({ localhost: "127.0.0.2", "loop.test": "127.0.0.1" });
  const host = kind.startsWith("localhost") ? "localhost" : kind.startsWith("name") ? "loop.test" : kind === "ipv6-http" ? "[::1]" : "127.0.0.1";
  const scheme = kind.endsWith("https") ? "https" : "http";
  try {
    await senders(m)[sender]!(`${scheme}://${host}:${port}`);
  } catch (error) { if (process.env.PROBE_DEBUG !== undefined) process.stderr.write(`${String(error).slice(0, 400)}\n`); }
  const blob = Buffer.concat(proxy.chunks).toString("latin1");
  process.stdout.write(`${JSON.stringify({
    connected: shim.connected, asked: shim.asked,
    targetBytes: target.markerBytes, targetConnections: target.connections,
    answeredBytes: answered.markerBytes, answeredConnections: answered.connections,
    proxyConnections: proxy.connections, proxyLine: blob.split("\r\n")[0] ?? "", port,
  })}\n`);
  process.exit(0);
}

void main();
