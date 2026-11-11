/**
 * The AI SDK sandbox session (src/sandbox-integrations/ai-sdk/session.ts) over the contract-driven mock API: the
 * exit-code table, the working folder and timeout rules, abort, the errors that propagate, dispose, and the file
 * methods. The session imports only types from `ai`, so the package is never loaded here. Synthetic credentials
 * only; no socket.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import type { Experimental_SandboxSession } from "ai";

import { FutureAGIClient } from "../../../futureagi-client";
import { CommandFailedError, CommandIncompleteError, Sandbox, SandboxError } from "../../../sandbox";
import { BASE, EXEC, SID, SandboxApi, json, sseText, streamed } from "../../../sandbox/__fixtures__/openapi-mock";
import {
  EXIT_CANCELLED,
  EXIT_FAILED,
  EXIT_SIGNAL_BASE,
  EXIT_TIMED_OUT,
  LINUX_SIGNALS,
  endingNote,
  shellExitCode,
  signalNumber,
} from "../exit";
import {
  clampTimeout,
  createFutureAGISandboxSession,
  filesPath,
  resolvePath,
  type FutureAGISandboxSession,
  type FutureAGISandboxSessionOptions,
} from "../session";

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
const ENV = [
  "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID",
  "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS",
  "OMEGA_BASE_URL", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
];
const START = ["started", { execId: EXEC, sandboxId: SID }, "1"] as const;
const EXIT = { exitCode: 0, timedOut: false, cancelled: false, truncated: false, durationMs: 3, stdoutBytes: 0, stderrBytes: 0 };
const exitFrame = (fields: Record<string, unknown> = {}) => ["exit", { ...EXIT, ...fields }, "9"] as const;
const ending = (fields: Partial<{ exitCode: number | null; signal: string; timedOut: boolean; cancelled: boolean; error: string }>) =>
  ({ exitCode: null, timedOut: false, cancelled: false, ...fields });

let saved: [string, string | undefined][] = [];
let api: SandboxApi;
let globalFetch: jest.SpyInstance;
beforeEach(() => {
  saved = ENV.map((key) => [key, process.env[key]]);
  for (const key of ENV) delete process.env[key];
  api = new SandboxApi();
  globalFetch = jest.spyOn(globalThis, "fetch").mockImplementation((input, init) => api.fetch(input as RequestInfo, init));
});
afterEach(() => {
  globalFetch.mockRestore();
  for (const [key, value] of saved) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  expect(api.problems).toEqual([]);
});

function client(): FutureAGIClient {
  const c = new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, platformBaseUrl: api.base, fetch: api.fetch });
  Object.assign(c._platform.shared, { sleep: async () => undefined });
  return c;
}
const hostedEnv = (): void => {
  Object.assign(process.env, { OMEGA_BASE_URL: BASE, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY });
};
const connect = (): Promise<Sandbox> => client().sandboxes.connect(SID);
const session = async (options: Omit<FutureAGISandboxSessionOptions, "sandbox" | "create"> = {}): Promise<FutureAGISandboxSession> =>
  createFutureAGISandboxSession({ sandbox: await connect(), ...options });
const execBodies = (): unknown[] => api.callsTo("execInWorkspaceSandbox").map((c) => c.json);
const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);
const until = async (done: () => boolean): Promise<void> => {
  for (let i = 0; i < 200 && !done(); i += 1) await new Promise((r) => setTimeout(r, 5));
};

describe("the exit-code table", () => {
  it.each([
    ["its own 0", ending({ exitCode: 0 }), 0],
    ["its own 3", ending({ exitCode: 3 }), 3],
    ["a timeout (with the SIGKILL that ended it)", ending({ timedOut: true, signal: "SIGKILL" }), EXIT_TIMED_OUT],
    ["SIGKILL", ending({ signal: "SIGKILL" }), EXIT_SIGNAL_BASE + 9],
    ["SIGTERM", ending({ signal: "SIGTERM" }), 143],
    ["a signal given as a number", ending({ signal: "9" }), 137],
    ["a cancel (over a timeout and its signal)", ending({ cancelled: true, timedOut: true, signal: "SIGKILL" }), EXIT_CANCELLED],
    ["a spawn error", ending({ error: "spawn /bin/nope ENOENT" }), EXIT_FAILED],
    ["a signal with no known number", ending({ signal: "SIGNOPE" }), EXIT_FAILED],
    ["no number at all", ending({}), EXIT_FAILED],
  ])("%s", (_label, result, code) => {
    expect(shellExitCode(result)).toBe(code);
  });

  it("names how a command ended when the code alone does not", () => {
    expect(endingNote(ending({ exitCode: 2 }))).toBeUndefined();
    expect(endingNote(ending({ timedOut: true }), 30)).toBe("Command timed out after 30 seconds");
    expect(endingNote(ending({ timedOut: true }))).toBe("Command timed out");
    expect(endingNote(ending({ cancelled: true }))).toBe("Command was cancelled");
    expect(endingNote(ending({ error: "ENOENT" }))).toBe("The command could not start: ENOENT");
    expect(endingNote(ending({ signal: "SIGTERM" }))).toBe("Command was ended by signal SIGTERM");
    expect(endingNote(ending({ signal: "SIGNOPE" }))).toBe("Command ended without an exit code (SIGNOPE)");
    expect(signalNumber("term")).toBe(15);
    expect(signalNumber(undefined)).toBeUndefined();
  });

  it("uses the same Linux signal table as the Python SDK", () => {
    const source = readFileSync(join(__dirname, "..", "..", "..", "..", "..", "..", "python", "fi", "sandbox", "types.py"), "utf8");
    const block = source.slice(source.indexOf("LINUX_SIGNALS = {"), source.indexOf("}", source.indexOf("LINUX_SIGNALS = {")));
    const python = Object.fromEntries([...block.matchAll(/"(SIG[A-Z0-9]+)": (\d+)/gu)].map((m) => [m[1]!, Number(m[2])]));
    expect(Object.keys(python).length).toBeGreaterThan(30);
    expect({ ...LINUX_SIGNALS }).toEqual(python);
  });
});

describe("run", () => {
  it("is an Experimental_SandboxSession of the pinned ai version (the compiler checks the assignment)", async () => {
    const sandbox: Experimental_SandboxSession = await session();
    expect(typeof sandbox.run).toBe("function");
    expect(sandbox.description).toContain(SID);
    expect(sandbox.description).toContain("/workspace");
  });

  it.each([
    ["0 passes through", { exitCode: 0 }, 0, ""],
    ["a non-zero code passes through", { exitCode: 7 }, 7, ""],
    ["a timeout is 124", { exitCode: null, signal: "SIGKILL", timedOut: true }, 124, "Command timed out after 30 seconds"],
    ["SIGKILL is 137", { exitCode: null, signal: "SIGKILL" }, 137, "Command was ended by signal SIGKILL"],
    ["a cancel is 130", { exitCode: null, signal: "SIGKILL", cancelled: true }, 130, "Command was cancelled"],
    ["a spawn error is 1", { exitCode: null, error: "spawn /bin/nope ENOENT" }, 1, "The command could not start: spawn /bin/nope ENOENT"],
    ["no number is 1", { exitCode: null }, 1, "Command ended without an exit code"],
  ] as const)("%s", async (_label, fields, code, note) => {
    api.on("execInWorkspaceSandbox", () =>
      streamed([sseText([START, ["stdout", { data: "out\n" }, "2"], ["stderr", { data: "err" }, "3"], exitFrame(fields)])]));
    const result = await (await session({ timeoutSeconds: 30 })).run({ command: "make" });
    expect(result).toEqual({ exitCode: code, stdout: "out\n", stderr: note === "" ? "err" : `err\n${note}` });
    expect(execBodies()).toHaveLength(1);
  });

  it("runs in /workspace by default; a per-call workingDirectory wins, and env passes through", async () => {
    const sbx = await session();
    await sbx.run({ command: "pwd" });
    await sbx.run({ command: "pwd", workingDirectory: "/tmp/build", env: { MODE: "test" } });
    await sbx.run({ command: "pwd", workingDirectory: "src/../lib" });
    expect(execBodies()).toEqual([
      { command: "pwd", cwd: "/workspace" },
      { command: "pwd", cwd: "/tmp/build", env: { MODE: "test" } },
      { command: "pwd", cwd: "/workspace/lib" },
    ]);
  });

  it("the session's own workingDirectory is the default", async () => {
    await (await session({ workingDirectory: "/workspace/app" })).run({ command: "ls" });
    expect(execBodies()).toEqual([{ command: "ls", cwd: "/workspace/app" }]);
  });

  it("timeoutSeconds is an integer of at least 1, capped to maxTimeoutSeconds; absent, none is sent", async () => {
    for (const [options, sent] of [
      [{}, undefined],
      [{ timeoutSeconds: 0 }, 1],
      [{ timeoutSeconds: 2.5 }, 3],
      [{ timeoutSeconds: 5000, maxTimeoutSeconds: 3600 }, 3600],
      [{ timeoutSeconds: 900, maxTimeoutSeconds: 3600 }, 900],
      [{ timeoutSeconds: 5000 }, 5000],
    ] as const) {
      await (await session(options)).run({ command: "true" });
      expect((execBodies().at(-1) as { timeoutSeconds?: number }).timeoutSeconds).toBe(sent);
    }
    expect(clampTimeout(Number.NaN)).toBeUndefined();
    expect(clampTimeout(-5, 10)).toBe(1);
  });

  it("an abort closes the stream (which cancels the command) and sends no second exec", async () => {
    let closed = false;
    api.on("execInWorkspaceSandbox", () =>
      streamed([sseText([START, ["stdout", { data: "tick" }, "2"]])], { hold: true, onCancel: () => { closed = true; } }));
    const sbx = await session();
    const controller = new AbortController();
    const running = failure(() => sbx.run({ command: "sleep 600", abortSignal: controller.signal }));
    await until(() => execBodies().length === 1);
    await new Promise((r) => setTimeout(r, 10));
    controller.abort(new Error("the agent stopped"));
    expect(await running).toBeInstanceOf(Error);
    await until(() => closed);
    expect(closed).toBe(true);
    expect(execBodies()).toHaveLength(1);
  });

  it("an already aborted signal sends nothing", async () => {
    const controller = new AbortController();
    controller.abort(new Error("stopped before it began"));
    expect(await failure(async () => (await session()).run({ command: "true", abortSignal: controller.signal }))).toBeInstanceOf(Error);
    expect(execBodies()).toHaveLength(0);
  });

  it("CommandIncompleteError (no exit frame) propagates and is not retried", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["stdout", { data: "partial" }, "2"]])]));
    const error = await failure(async () => (await session()).run({ command: "long" }));
    expect(error).toBeInstanceOf(CommandIncompleteError);
    expect(error).toMatchObject({ stdout: "partial", execId: EXEC });
    expect(execBodies()).toHaveLength(1);
  });

  it("CommandFailedError (an error frame) propagates and is not retried", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["error", { message: "runtime lost" }, "2"]])]));
    const error = await failure(async () => (await session()).run({ command: "x" }));
    expect(error).toBeInstanceOf(CommandFailedError);
    expect((error as Error).message).toContain("runtime lost");
    expect(execBodies()).toHaveLength(1);
  });

  it("a refused request propagates as the handle's error, sent once", async () => {
    api.on("execInWorkspaceSandbox", () => json(409, { code: "conflict", message: "the sandbox is hibernated", detail: { state: "hibernated" } }));
    expect(await failure(async () => (await session()).run({ command: "x" }))).toBeInstanceOf(SandboxError);
    expect(execBodies()).toHaveLength(1);
  });

  it("spawn is not offered: it rejects before anything is sent", async () => {
    const sbx = await session();
    const error = await failure(() => sbx.spawn({ command: "npm run dev" }));
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ code: "not_offered" });
    expect(api.calls.filter((c) => c.operation.operationId !== "getWorkspaceSandbox")).toHaveLength(0);
  });
});

describe("dispose", () => {
  const deletes = (): number => api.callsTo("destroyWorkspaceSandbox").length;

  it("deletes a sandbox the function created, once", async () => {
    hostedEnv();
    const sbx = await createFutureAGISandboxSession({ create: { name: "agent" } });
    expect(api.callsTo("createWorkspaceSandbox")[0]!.json).toEqual({ name: "agent" });
    expect(sbx.sandbox.id).toBe(SID);
    await sbx.dispose();
    await sbx.dispose();
    expect(deletes()).toBe(1);
  });

  it("creates from the environment with no options at all", async () => {
    hostedEnv();
    const sbx = await createFutureAGISandboxSession();
    expect(api.callsTo("createWorkspaceSandbox")).toHaveLength(1);
    await sbx[Symbol.asyncDispose]();
    expect(deletes()).toBe(1);
  });

  it("never deletes a sandbox it was given, unless deleteOnDispose is set", async () => {
    await (await session()).dispose();
    expect(deletes()).toBe(0);
    await (await session({ deleteOnDispose: true })).dispose();
    expect(deletes()).toBe(1);
  });

  it("keeps a created sandbox when deleteOnDispose is false", async () => {
    hostedEnv();
    await (await createFutureAGISandboxSession({ deleteOnDispose: false }))[Symbol.asyncDispose]();
    expect(deletes()).toBe(0);
  });

  it("Symbol.asyncDispose deletes like dispose", async () => {
    const sbx = await session({ deleteOnDispose: true });
    await sbx[Symbol.asyncDispose]();
    expect(deletes()).toBe(1);
  });

  it("refuses sandbox and create together, before any request", async () => {
    const sandbox = await connect();
    const before = api.calls.length;
    expect(await failure(() => createFutureAGISandboxSession({ sandbox, create: { name: "x" } }))).toBeInstanceOf(TypeError);
    expect(api.calls).toHaveLength(before);
  });
});

describe("files", () => {
  const bytes = (text: string): Response =>
    new Response(new TextEncoder().encode(text), { status: 200, headers: { "content-type": "application/octet-stream" } });

  it("paths resolve against the working folder and are sent relative to /workspace", () => {
    expect(resolvePath("/workspace", "a/./b/../c.txt")).toBe("/workspace/a/c.txt");
    expect(resolvePath("/workspace/app", "/etc/hosts")).toBe("/etc/hosts");
    expect(filesPath("/workspace", "src/a.ts")).toBe("src/a.ts");
    expect(filesPath("/workspace/app", "/workspace/b.txt")).toBe("b.txt");
    expect(filesPath("/workspace", ".")).toBe(".");
    expect(() => filesPath("/workspace", "/etc/hosts")).toThrow(SandboxError);
  });

  it("readTextFile decodes the file and keeps a 1-based inclusive line range", async () => {
    api.on("downloadWorkspaceSandboxFile", () => bytes("one\ntwo\nthree\n"));
    const sbx = await session();
    expect(await sbx.readTextFile({ path: "notes/a.txt" })).toBe("one\ntwo\nthree\n");
    expect(await sbx.readTextFile({ path: "notes/a.txt", startLine: 2, endLine: 2 })).toBe("two\n");
    expect(await sbx.readTextFile({ path: "notes/a.txt", startLine: 2, endLine: 99 })).toBe("two\nthree\n");
    expect(api.callsTo("downloadWorkspaceSandboxFile").map((c) => c.params.path)).toEqual(["notes/a.txt", "notes/a.txt", "notes/a.txt"]);
  });

  it("readBinaryFile and readFile return the bytes; a missing file is null", async () => {
    api.on("downloadWorkspaceSandboxFile",
      () => new Response(new Uint8Array([0, 1, 2, 255]), { status: 200, headers: { "content-type": "application/octet-stream" } }),
      () => json(404, { code: "not_found", message: "no such file" }));
    const sbx = await session();
    const stream = await sbx.readFile({ path: "/workspace/a.bin" });
    expect(Array.from(new Uint8Array(await new Response(stream).arrayBuffer()))).toEqual([0, 1, 2, 255]);
    expect(await sbx.readBinaryFile({ path: "gone.bin" })).toBeNull();
    expect(await sbx.readTextFile({ path: "gone.txt" })).toBeNull();
    expect(await sbx.readFile({ path: "gone.txt" })).toBeNull();
  });

  it("a path outside /workspace is refused before anything is sent", async () => {
    const sbx = await session();
    expect(await failure(() => sbx.readTextFile({ path: "/etc/passwd" }))).toBeInstanceOf(SandboxError);
    expect(await failure(() => sbx.writeTextFile({ path: "/etc/motd", content: "x" }))).toBeInstanceOf(SandboxError);
    expect(api.callsTo("downloadWorkspaceSandboxFile")).toHaveLength(0);
    expect(api.callsTo("writeWorkspaceSandboxFile")).toHaveLength(0);
  });

  it("writeTextFile, writeBinaryFile and writeFile write once each (missing folders are the server's to create)", async () => {
    const sbx = await session({ workingDirectory: "/workspace/app" });
    await sbx.writeTextFile({ path: "src/a.txt", content: "hi" });
    await sbx.writeBinaryFile({ path: "/workspace/b.bin", content: new Uint8Array([0, 1, 2, 255]) });
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new Uint8Array([0, 1]));
        controller.enqueue(new Uint8Array([2, 255]));
        controller.close();
      },
    });
    await sbx.writeFile({ path: "c.bin", content: stream });
    const writes = api.callsTo("writeWorkspaceSandboxFile");
    expect(writes.map((c) => [c.params.path, c.json])).toEqual([
      ["app/src/a.txt", { content: "hi", encoding: "utf8" }],
      ["b.bin", { content: "AAEC/w==", encoding: "base64" }],
      ["app/c.bin", { content: "AAEC/w==", encoding: "base64" }],
    ]);
    expect(api.callsTo("createWorkspaceSandboxFolder")).toHaveLength(0);
    expect(await failure(() => sbx.writeTextFile({ path: "d.txt", content: "x", encoding: "latin1" }))).toBeInstanceOf(TypeError);
  });
});
