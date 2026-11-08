/**
 * Loading the SDK under test BY PATH, so a suite run can target any build of the SDK
 * (a source checkout, a built package or a wheel).
 *
 * The binding contract (README "Bindings"): the SDK package ships a small adapter that maps a
 * case's `x-omega-sdk {family, method}` name and neutral `args` onto its public API.
 *
 *   TypeScript and the fake:  <dir>/conformance/binding.mjs exporting
 *     createClient({ baseUrl, credential, fetch, options }) -> client
 *     call(client, { family, method }, args, { idempotencyKey }) -> value (throws the SDK's error)
 *     describeError(error) -> { errorClass, status, code, requestId, upstreamRequestId, possiblyApplied }
 *     clientCase?(spec, { fetch }) -> { errorClass?, networkRequests }      (client-side must-exist cases)
 *   Python: a module named by --binding-module (default: futureagi_omega.conformance_binding, then
 *     omega_agents.conformance_binding, then conformance_binding) with the same four functions,
 *     driven by runners/py/worker.py over JSON lines.
 *
 * `--client-ts <built packages/client dir>`, `--testkit <dir>` and `--client-py <wheel or source dir>`.
 */
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** The ESM entry of a package directory (exports["."] import/default, else module, else main). */
export function packageEntry(dir) {
  const pkg = JSON.parse(readFileSync(path.join(dir, "package.json"), "utf8"));
  const dot = typeof pkg.exports === "string" ? pkg.exports : pkg.exports?.["."];
  const entry = typeof dot === "string" ? dot : dot?.import ?? dot?.default ?? pkg.module ?? pkg.main ?? "index.js";
  return { name: pkg.name, version: pkg.version, entry: path.resolve(dir, typeof entry === "string" ? entry : entry.default) };
}

/** Load a TS/JS binding from a package directory. */
export async function loadJsBinding(dir) {
  const resolved = path.resolve(dir);
  const binding = path.join(resolved, "conformance", "binding.mjs");
  if (!existsSync(binding)) throw new Error(`${resolved} has no conformance/binding.mjs (the binding contract in tests/platform-conformance/README.md)`);
  const pkg = packageEntry(resolved);
  const module = await import(pathToFileURL(binding).href);
  for (const name of ["createClient", "call", "describeError"]) {
    if (typeof module[name] !== "function") throw new Error(`${binding} does not export ${name}()`);
  }
  return { kind: "js", package: { name: pkg.name, version: pkg.version, dir: resolved }, binding: module };
}

/**
 * Start the Python worker for a wheel or source directory. Returns a binding with the same shape
 * as a JS one, whose calls cross a JSON-lines pipe (the egress guard is armed inside the worker).
 */
export function startPythonBinding({ client, python = "python3", bindingModule, allow = [] }) {
  const worker = path.join(HERE, "..", "py", "worker.py");
  const args = ["-I", "-B", worker, "--client-py", path.resolve(client), "--allow", allow.join(",")];
  if (bindingModule) args.push("--binding-module", bindingModule);
  const child = spawn(python, args, { stdio: ["pipe", "pipe", "inherit"] });
  const lines = createInterface({ input: child.stdout });
  const waiting = new Map();
  let next = 0;
  let ready;
  const readyPromise = new Promise((resolve, reject) => {
    ready = { resolve, reject };
    child.once("exit", (code) => reject(new Error(`the Python worker exited (${code}) before it was ready`)));
  });
  lines.on("line", (line) => {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }
    if (message.ready) return ready.resolve(message);
    const pending = waiting.get(message.id);
    if (pending) {
      waiting.delete(message.id);
      pending(message);
    }
  });
  const request = (payload) => new Promise((resolve) => {
    const id = ++next;
    waiting.set(id, resolve);
    child.stdin.write(`${JSON.stringify({ id, ...payload })}\n`);
  });
  return readyPromise.then((hello) => ({
    kind: "py",
    package: hello.package,
    binding: {
      createClient: (options) => ({ remote: options }),
      call: async (client, sdk, args, opts) => {
        const reply = await request({ op: "call", client: client.remote, sdk, args, opts });
        if (reply.error) throw Object.assign(new Error(reply.error.message ?? "sdk error"), { described: reply.error });
        return reply.value;
      },
      describeError: (error) => error.described ?? { errorClass: "SDKException", message: error.message },
      clientCase: async (spec) => (await request({ op: "clientCase", spec })).value,
    },
    guardReceipt: async () => (await request({ op: "guard" })).value,
    close: () => {
      child.stdin.end();
      return new Promise((resolve) => child.once("exit", resolve));
    },
  }));
}
