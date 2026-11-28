import { execFile, execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import dns from "node:dns";
import { once } from "node:events";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire, syncBuiltinESMExports } from "node:module";
import net from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import tls from "node:tls";
import { fileURLToPath, pathToFileURL } from "node:url";
import { promisify } from "node:util";

const file = fileURLToPath(import.meta.url);
const root = join(dirname(file), "../../..");
const requireHere = createRequire(import.meta.url);
const run = promisify(execFile);
const LOCAL = "127.0.0.1";
const NAMED = "load-path.test";

function listen(server) {
  server.listen(0, LOCAL);
  return once(server, "listening");
}

function sink(marker, material) {
  let connections = 0;
  const chunks = [];
  const sockets = new Set();
  const receive = (socket) => {
    let head = Buffer.alloc(0);
    socket.on("data", (chunk) => {
      chunks.push(chunk);
      head = Buffer.concat([head, chunk]);
      if (head.includes("\r\n\r\n")) {
        socket.end("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");
      }
    });
  };
  const server = material === undefined ? net.createServer(receive) : tls.createServer(material, receive);
  server.on("connection", (socket) => {
    connections += 1;
    sockets.add(socket);
    socket.on("error", () => undefined);
    socket.once("close", () => { sockets.delete(socket); });
  });
  return {
    listen: () => listen(server),
    port: () => server.address().port,
    reset: () => { connections = 0; chunks.length = 0; },
    counts: () => {
      const data = Buffer.concat(chunks);
      return { connections, bytes: data.length, markers: data.toString("latin1").split(marker).length - 1 };
    },
    close: () => {
      for (const socket of sockets) socket.destroy();
      return new Promise((resolve) => server.close(resolve));
    },
  };
}

/** A per-run CA and a leaf valid for both test hostnames. */
function certificates(at) {
  const openssl = (...args) => execFileSync("openssl", args, { cwd: at, stdio: "pipe" });
  const ec = ["-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes"];
  openssl("req", "-x509", ...ec, "-days", "1", "-subj", "/CN=SDK test CA", "-keyout", "ca.pem", "-out", "trust.pem");
  openssl("req", "-new", ...ec, "-subj", `/CN=${NAMED}`, "-keyout", "leaf.pem", "-out", "leaf.csr");
  writeFileSync(join(at, "extensions.cnf"), `subjectAltName=DNS:${NAMED},IP:${LOCAL}\nextendedKeyUsage=serverAuth\n`);
  openssl("x509", "-req", "-in", "leaf.csr", "-CA", "trust.pem", "-CAkey", "ca.pem", "-CAcreateserial", "-days", "1", "-extfile", "extensions.cnf", "-out", "leaf.crt");
  return { cert: readFileSync(join(at, "leaf.crt")), key: readFileSync(join(at, "leaf.pem")) };
}

function childEnv(proxy, trust) {
  const env = { ...process.env };
  for (const name of Object.keys(env)) {
    if (/^(?:(?:http|https|all|no)_proxy|node_use_env_proxy|node_extra_ca_certs|node_tls_reject_unauthorized|fi_allow_insecure_http)$/iu.test(name)) delete env[name];
  }
  const via = `http://${LOCAL}:${proxy.port()}`;
  // Observe the proxy listener while isolating dispatcher selection from proxy-variable routing.
  Object.assign(env, { HTTP_PROXY: via, HTTPS_PROXY: via, ALL_PROXY: via, NO_PROXY: `${LOCAL},${NAMED}` });
  if (trust !== undefined) env.NODE_EXTRA_CA_CERTS = trust;
  return env;
}

async function scenario(hostKind, slot, ...remedies) {
  const at = mkdtempSync(join(tmpdir(), "sdk-load-path-"));
  const marker = `marker-${randomUUID()}`;
  const target = sink(marker);
  const proxy = sink(marker);
  let secure;
  try {
    if (remedies.some((step) => step.startsWith("https"))) secure = sink(marker, certificates(at));
    const sinks = secure === undefined ? [target, proxy] : [target, proxy, secure];
    await Promise.all(sinks.map((listener) => listener.listen()));
    const steps = {};
    for (const step of ["initial", ...remedies]) {
      for (const listener of sinks) listener.reset();
      const encrypted = step.startsWith("https");
      const listener = encrypted ? secure : target;
      const host = hostKind === "named" ? NAMED : LOCAL;
      const base = `${encrypted ? "https" : "http"}://${host}:${listener.port()}`;
      const mode = step.startsWith("commonjs") ? "cjs" : step === "builtin" ? "esm-with-builtin" : "esm";
      const placement = step === "commonjs-global" ? "global" : slot;
      const env = childEnv(proxy, encrypted ? join(at, "trust.pem") : undefined);
      const graphAt = mkdtempSync(join(at, "graph-"));
      const { stdout } = await run(process.execPath, [requireHere.resolve("tsx/cli"), file, "send", mode, placement, base, marker, graphAt], { cwd: root, env, timeout: 15_000 });
      const result = JSON.parse(stdout);
      steps[step] = { ...result, target: listener.counts(), proxy: proxy.counts() };
    }
    return steps;
  } finally {
    await Promise.all([target.close(), proxy.close(), secure?.close()]);
    rmSync(at, { recursive: true, force: true });
  }
}

/** Link a static ES module graph after the process loader has been configured. */
async function loadGraph(mode, at, source) {
  if (mode === "cjs") return Object.fromEntries(Object.entries(source).map(([name, path]) => [name, requireHere(path)]));
  const entry = join(at, "sdk-entry.mjs");
  writeFileSync(entry, Object.entries(source).map(([name, path]) => `import * as ${name} from ${JSON.stringify(pathToFileURL(path).href)}; export { ${name} };`).join("\n"));
  return import(pathToFileURL(entry).href);
}

function loadPlatform(mode, at) {
  return loadGraph(mode, at, {
    platform: join(root, "src/platform/index.ts"),
    loader: join(root, "src/_core/module-loader.ts"),
  });
}

async function send(mode, placement, baseUrl, marker, at) {
  // All named dials use this shim, including the native fetch and undici Agent paths.
  dns.lookup = (host, options, callback) => {
    const done = callback ?? options;
    queueMicrotask(() => {
      if (host !== NAMED && host !== LOCAL) return done(new Error("Unexpected test hostname"));
      if (options?.all) return done(null, [{ address: LOCAL, family: 4 }]);
      return done(null, LOCAL, 4);
    });
  };
  syncBuiltinESMExports();
  void Request;
  const undici = placement === "none" ? undefined : requireHere("undici");
  const agent = undici && new undici.Agent();
  if (placement === "global") undici.setGlobalDispatcher(agent);
  if (placement === "foreign") undici.setGlobalDispatcher({ dispatch: agent.dispatch.bind(agent) });
  if (mode !== "esm-with-builtin") delete process.getBuiltinModule;
  const usingBuiltin = typeof process.getBuiltinModule === "function";
  try {
    const graph = await loadPlatform(mode, at);
    const moduleForm = Object.prototype.toString.call(graph.loader) === "[object Module]" ? "esm" : "cjs";
    const loaderReadsHttp = graph.loader.loadModule("node:http") === requireHere("node:http");
    const observed = { moduleForm, usingBuiltin, loaderReadsHttp };
    try {
      const client = new graph.platform.Client({
        baseUrl, apiKey: marker, secretKey: "test-secret", allowInsecureHttp: true, maxRetries: 0, timeout: 3000,
      });
      await client.request("GET", "/probe");
      return { ...observed, outcome: "delivered" };
    } catch (error) {
      const message = String(error?.message ?? error);
      return {
        ...observed, outcome: error?.name,
        code: error?.code ?? /\((insecure_http_origin)\)/u.exec(message)?.[1],
        markerInMessage: message.includes(marker), message: message.replaceAll(marker, "[marker]"),
      };
    }
  } finally {
    await agent?.destroy();
  }
}

if (process.argv[1] === file) {
  const [action, ...args] = process.argv.slice(2);
  const result = await (action === "send" ? send(...args) : scenario(...args));
  process.stdout.write(`${JSON.stringify(result)}\n`, () => process.exit(0));
}
