// Run one catalog case and return its observation.
// A case is {id, area, fn: async (ctx) => value, env?, replies?}.
import { spawnSync } from "node:child_process";
import { Determinism } from "./determinism.mjs";
import { clean, observe } from "./observe.mjs";
import { Wire } from "./wire.mjs";

export const KEY = "parity-gateway-key"; // never a credential shape
export const BASE_URL = "https://gateway.example.test";
const ENV_PREFIXES = ["AGENTCC_", "FI_", "OPENAI_"];
export const OMIT = Symbol("omit");
// Loads the target's main package in a fresh process and prints one export.
const LOADER = new URL("./load.mjs", import.meta.url).href;
const CHILD = [
  "const [loader, install, name, format, key] = process.argv.slice(1);",
  "const { load } = await import(loader);",
  "const r = await load(install, name, '.', format);",
  "console.log(r.ok ? String(r.module[key] ?? '<absent>') : '<load failed: ' + r.error.name + '>');",
].join("\n");

export class Ctx {
  constructor(target, wire) {
    this.target = target;
    this.mod = target.module;
    this.wire = wire;
  }

  client(opts = {}) {
    if (!this.mod) throw Object.assign(new Error("main module failed to load"), { load: this.target.mainLoad });
    const merged = { apiKey: KEY, baseUrl: BASE_URL, ...opts };
    for (const [k, v] of Object.entries(merged)) if (v === OMIT) delete merged[k];
    return new this.mod.AgentCC(merged);
  }

  async sub(subpath) {
    return this.target.loadSub(subpath);
  }

  script(...replies) {
    this.wire.script(...replies);
  }

  async drain(iterable, limit = 200) {
    const items = [];
    let error = null;
    try {
      for await (const item of iterable) {
        items.push(observe(item));
        if (items.length >= limit) break;
      }
    } catch (err) {
      error = observe(err);
    }
    return { items, error };
  }

  // A value the package computes once, when it loads (the twin of Python's
  // subprocess import): a fresh Node process inherits only this case's
  // variables (runCase has isolated process.env) and prints the export.
  importTime(key) {
    const { install, format, main } = this.target.child ?? {};
    if (!install) throw new Error("importTime needs target.child {install, format, main}");
    const done = spawnSync(process.execPath, ["--input-type=module", "-e", CHILD, LOADER, install, main, format, key], { env: process.env, encoding: "utf8", timeout: 120_000 });
    return { exit: done.status, stdout: done.stdout.trim(), stderr_tail: done.stderr.trim().split("\n").filter(Boolean).slice(-1).map(clean) };
  }

  async attempt(fn) {
    try {
      return { ok: observe(await fn()) };
    } catch (err) {
      return { raised: observe(err) };
    }
  }
}

function isolateEnv(extra) {
  const saved = { ...process.env };
  for (const key of Object.keys(process.env)) if (ENV_PREFIXES.some((p) => key.startsWith(p))) delete process.env[key];
  Object.assign(process.env, extra);
  return saved;
}

function restoreEnv(saved) {
  for (const key of Object.keys(process.env)) if (!(key in saved)) delete process.env[key];
  Object.assign(process.env, saved);
}

function captureConsole() {
  const lines = [];
  const saved = {};
  for (const level of ["log", "info", "warn", "error", "debug"]) {
    saved[level] = console[level];
    console[level] = (...args) => lines.push([level, clean(args.map((a) => (typeof a === "string" ? a : JSON.stringify(observe(a)))).join(" "))]);
  }
  const savedEmit = process.emitWarning;
  process.emitWarning = (warning, opts) => lines.push(["emitWarning", clean(String(warning?.message ?? warning)), observe(opts)]);
  return {
    lines,
    restore() {
      Object.assign(console, saved);
      process.emitWarning = savedEmit;
    },
  };
}

export async function runCase(testCase, target) {
  const saved = isolateEnv(testCase.env ?? {});
  const det = new Determinism();
  const wire = new Wire(det);
  wire.script(...(testCase.replies ?? []));
  const out = {};
  const consoleCapture = captureConsole();
  try {
    wire.install();
    det.install();
    const ctx = new Ctx(target, wire);
    try {
      out.result = observe(await testCase.fn(ctx));
    } catch (err) {
      out.raised = observe(err);
    }
    await new Promise((r) => setImmediate(r));
  } finally {
    det.remove();
    wire.remove();
    consoleCapture.restore();
    restoreEnv(saved);
  }
  out.requests = wire.requests;
  Object.assign(out, det.report());
  if (consoleCapture.lines.length) out.console = consoleCapture.lines;
  if (wire.replies.length) out.unused_replies = wire.replies.length;
  return out;
}
