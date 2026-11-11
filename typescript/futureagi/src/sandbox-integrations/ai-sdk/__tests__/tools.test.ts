/**
 * The AI SDK sandbox tools (src/sandbox-integrations/ai-sdk/tools.ts) over the contract-driven mock API: names,
 * input schemas, results (the Python MCP server's, design 3.4), clipping, timeouts, paths and errors. `ai` is
 * mocked (its `tool` is the identity and `jsonSchema` keeps the schema), so the package is never loaded here.
 * Synthetic credentials only; no socket.
 */
import type { Tool } from "ai";

import { FutureAGIClient } from "../../../futureagi-client";
import { CommandIncompleteError, QuotaExceededError, Sandbox, SandboxError } from "../../../sandbox";
import { EXEC, SID, SandboxApi, json, sseText, streamed } from "../../../sandbox/__fixtures__/openapi-mock";
import { clipOutput, DEFAULT_MAX_OUTPUT_CHARS, sandboxTools, type SandboxTools, type SandboxToolsOptions } from "../tools";

jest.mock("ai", () => ({
  tool: (definition: unknown) => definition,
  jsonSchema: (schema: unknown) => ({ jsonSchema: schema }),
}));

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
const START = ["started", { execId: EXEC, sandboxId: SID }, "1"] as const;
const EXIT = { exitCode: 0, timedOut: false, cancelled: false, truncated: false, durationMs: 3, stdoutBytes: 0, stderrBytes: 0 };
const OPTIONS = { toolCallId: "call_1", messages: [], context: {} };
const NAMES = ["sandbox_exec", "sandbox_read_file", "sandbox_write_file", "sandbox_list_files"];
const ENV = [
  "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID",
  "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS",
  "OMEGA_BASE_URL", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
];

let saved: [string, string | undefined][] = [];
let api: SandboxApi;
beforeEach(() => {
  saved = ENV.map((key) => [key, process.env[key]]);
  for (const key of ENV) delete process.env[key];
  api = new SandboxApi();
});
afterEach(() => {
  for (const [key, value] of saved) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  expect(api.problems).toEqual([]);
});

async function tools(options: SandboxToolsOptions = {}): Promise<SandboxTools> {
  const client = new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, platformBaseUrl: api.base, fetch: api.fetch });
  Object.assign(client._platform.shared, { sleep: async () => undefined });
  const sandbox: Sandbox = await client.sandboxes.connect(SID);
  return sandboxTools(sandbox, options);
}
/** Run one tool the way the AI SDK does (its `execute` with the call options). */
async function call(t: Tool, input: unknown): Promise<unknown> {
  return t.execute!(input, OPTIONS);
}
const schemaOf = (t: Tool): unknown => (t.inputSchema as unknown as { jsonSchema: unknown }).jsonSchema;
const execBodies = (): unknown[] => api.callsTo("execInWorkspaceSandbox").map((c) => c.json);
const failure = (run: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(run).then(() => undefined, (e: unknown) => e);

describe("names and input schemas", () => {
  it("offers the four tools of the Python MCP server's pinned mode, and nothing that takes env", async () => {
    const set = await tools();
    expect(Object.keys(set)).toEqual(NAMES);
    for (const name of NAMES) {
      const t = set[name as keyof SandboxTools] as Tool;
      expect(typeof t.execute).toBe("function");
      expect(typeof t.description).toBe("string");
      expect(Object.keys((schemaOf(t) as { properties: object }).properties)).not.toContain("env");
    }
  });

  it("declares each input schema", async () => {
    const set = await tools();
    expect(schemaOf(set.sandbox_exec)).toEqual({
      type: "object",
      properties: {
        command: { type: "string", description: expect.any(String) },
        cwd: { type: "string", description: expect.stringContaining("/workspace") },
        timeout_seconds: { type: "integer", minimum: 1, description: expect.any(String) },
      },
      required: ["command"],
      additionalProperties: false,
    });
    expect(schemaOf(set.sandbox_read_file)).toEqual({
      type: "object",
      properties: { path: { type: "string", description: expect.any(String) }, max_bytes: { type: "integer", minimum: 1, description: expect.any(String) } },
      required: ["path"],
      additionalProperties: false,
    });
    expect(schemaOf(set.sandbox_write_file)).toEqual({
      type: "object",
      properties: {
        path: { type: "string", description: expect.any(String) },
        content: { type: "string", description: expect.any(String) },
        encoding: { type: "string", enum: ["utf8", "base64"], description: expect.any(String) },
      },
      required: ["path", "content"],
      additionalProperties: false,
    });
    expect(schemaOf(set.sandbox_list_files)).toEqual({
      type: "object",
      properties: { path: { type: "string", description: expect.any(String) } },
      additionalProperties: false,
    });
    expect(set.sandbox_exec.description).not.toMatch(/900/u);
  });
});

describe("sandbox_exec", () => {
  it("returns the whole exit record with the MCP result keys; a timeout is a result", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["stdout", { data: "so far" }, "2"],
      ["exit", { ...EXIT, exitCode: null, signal: "SIGKILL", timedOut: true, durationMs: 30_000, stdoutBytes: 6 }, "3"]])]));
    const result = await call((await tools()).sandbox_exec, { command: "sleep 99", timeout_seconds: 30 });
    expect(result).toEqual({
      exit_code: null, signal: "SIGKILL", timed_out: true, cancelled: false, truncated: false, duration_ms: 30_000,
      error: null, exec_id: EXEC, stdout: "so far", stderr: "", stdout_clipped: false, stderr_clipped: false,
    });
    expect(execBodies()).toEqual([{ command: "sleep 99", cwd: "/workspace", timeoutSeconds: 30 }]);
  });

  it("a non-zero exit and a spawn error are results too", async () => {
    api.on("execInWorkspaceSandbox",
      () => streamed([sseText([START, ["stderr", { data: "no" }, "2"], ["exit", { ...EXIT, exitCode: 2, stderrBytes: 2 }, "3"]])]),
      () => streamed([sseText([START, ["exit", { ...EXIT, exitCode: null, error: "spawn ENOENT" }, "2"]])]));
    const set = await tools();
    expect(await call(set.sandbox_exec, { command: "false" })).toMatchObject({ exit_code: 2, stderr: "no", signal: null, error: null });
    expect(await call(set.sandbox_exec, { command: "nope" })).toMatchObject({ exit_code: null, error: "spawn ENOENT" });
  });

  it("cwd resolves against the working folder; timeouts are at least 1 and capped to maxTimeoutSeconds", async () => {
    const set = await tools({ workingDirectory: "/workspace/app", timeoutSeconds: 60, maxTimeoutSeconds: 3600 });
    await call(set.sandbox_exec, { command: "ls" });
    await call(set.sandbox_exec, { command: "ls", cwd: "src", timeout_seconds: 0 });
    await call(set.sandbox_exec, { command: "ls", cwd: "/tmp", timeout_seconds: 5000 });
    expect(execBodies()).toEqual([
      { command: "ls", cwd: "/workspace/app", timeoutSeconds: 60 },
      { command: "ls", cwd: "/workspace/app/src", timeoutSeconds: 1 },
      { command: "ls", cwd: "/tmp", timeoutSeconds: 3600 },
    ]);
  });

  it("keeps the newest maxOutputChars of each stream and says how many were dropped", async () => {
    api.on("execInWorkspaceSandbox", () =>
      streamed([sseText([START, ["stdout", { data: "abcdefghij" }, "2"], ["stderr", { data: "xyz" }, "3"], ["exit", EXIT, "4"]])]));
    const result = await call((await tools({ maxOutputChars: 5 })).sandbox_exec, { command: "seq" });
    expect(result).toMatchObject({
      stdout: "[... 5 earlier characters dropped ...]\nfghij", stdout_clipped: true, stderr: "xyz", stderr_clipped: false,
    });
    expect(DEFAULT_MAX_OUTPUT_CHARS).toBe(20_000);
    expect(clipOutput("a😀b", 2)).toEqual({ text: "[... 3 earlier characters dropped ...]\nb", clipped: true });
  });

  it("sends one exec per call and lets a stream with no exit frame throw", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START])]));
    expect(await failure(async () => call((await tools()).sandbox_exec, { command: "x" }))).toBeInstanceOf(CommandIncompleteError);
    expect(execBodies()).toHaveLength(1);
  });

  it("a refusal is thrown as the handle's error, sent once", async () => {
    api.on("execInWorkspaceSandbox", () => json(409, { code: "quota_exceeded", message: "full", detail: { scope: "org" } }));
    const error = await failure(async () => call((await tools()).sandbox_exec, { command: "x" }));
    expect(error).toBeInstanceOf(QuotaExceededError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(execBodies()).toHaveLength(1);
  });
});

describe("file tools", () => {
  it("sandbox_read_file returns text as utf8 and other files as base64, bounded by max_bytes", async () => {
    api.on("readWorkspaceSandboxFile",
      () => api.ok("readWorkspaceSandboxFile", { file: { path: "a.txt", encoding: "utf8", content: "hello" } }),
      () => api.ok("readWorkspaceSandboxFile", { file: { path: "a.bin", encoding: "base64", content: "AAEC/w==", bytes: 4 } }));
    const set = await tools();
    expect(await call(set.sandbox_read_file, { path: "a.txt", max_bytes: 100 })).toEqual({ path: "/workspace/a.txt", encoding: "utf8", content: "hello" });
    expect(await call(set.sandbox_read_file, { path: "/workspace/a.bin" })).toEqual({ path: "/workspace/a.bin", encoding: "base64", content: "AAEC/w==" });
    const reads = api.callsTo("readWorkspaceSandboxFile");
    expect(reads.map((c) => c.params.path)).toEqual(["a.txt", "a.bin"]);
    expect(reads[0]!.query.get("maxBytes")).toBe("100");
    expect(reads[1]!.query.get("maxBytes")).toBeNull();
  });

  it("sandbox_write_file writes text or base64 once, with no folder call, and returns the path and byte count", async () => {
    api.on("writeWorkspaceSandboxFile",
      () => api.ok("writeWorkspaceSandboxFile", { file: { path: "app/notes.md", bytes: 2 } }),
      () => api.ok("writeWorkspaceSandboxFile", { file: { path: "app/a.bin", bytes: 4 } }));
    const set = await tools({ workingDirectory: "/workspace/app" });
    expect(await call(set.sandbox_write_file, { path: "notes.md", content: "hi" })).toEqual({ path: "/workspace/app/notes.md", bytes: 2 });
    expect(await call(set.sandbox_write_file, { path: "a.bin", content: "AAEC/w==", encoding: "base64" })).toEqual({ path: "/workspace/app/a.bin", bytes: 4 });
    const writes = api.callsTo("writeWorkspaceSandboxFile");
    expect(writes.map((c) => [c.params.path, c.json])).toEqual([
      ["app/notes.md", { content: "hi", encoding: "utf8" }],
      ["app/a.bin", { content: "AAEC/w==", encoding: "base64" }],
    ]);
    expect(api.callsTo("createWorkspaceSandboxFolder")).toHaveLength(0);
  });

  it("sandbox_list_files lists the working folder by default with the MCP entry keys", async () => {
    api.on("listWorkspaceSandboxFiles", () => api.ok("listWorkspaceSandboxFiles", {
      path: ".",
      entries: [{ name: "src", size: 0, mode: "drwxr-xr-x", directory: true }, { name: "a.txt", size: 5, mode: "-rw-r--r--" }],
    }));
    const set = await tools();
    expect(await call(set.sandbox_list_files, {})).toEqual({
      path: "/workspace",
      entries: [
        { name: "src", size: 0, directory: true, mode: "drwxr-xr-x" },
        { name: "a.txt", size: 5, directory: false, mode: "-rw-r--r--" },
      ],
    });
    await call(set.sandbox_list_files, { path: "src" });
    expect(api.callsTo("listWorkspaceSandboxFiles").map((c) => c.query.get("path"))).toEqual([".", "src"]);
  });

  it("a path outside /workspace is refused before anything is sent", async () => {
    const set = await tools();
    expect(await failure(() => call(set.sandbox_read_file, { path: "/etc/passwd" }))).toBeInstanceOf(SandboxError);
    expect(await failure(() => call(set.sandbox_write_file, { path: "../etc/x", content: "x" }))).toBeInstanceOf(SandboxError);
    expect(api.callsTo("readWorkspaceSandboxFile")).toHaveLength(0);
    expect(api.callsTo("writeWorkspaceSandboxFile")).toHaveLength(0);
  });

  it("a missing file is the handle's NotFoundError", async () => {
    api.on("readWorkspaceSandboxFile", () => json(404, { code: "not_found", message: "no such file" }));
    const error = await failure(async () => call((await tools()).sandbox_read_file, { path: "gone.txt" }));
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ status: 404 });
  });
});
