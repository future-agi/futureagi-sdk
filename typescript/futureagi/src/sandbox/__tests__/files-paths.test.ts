/**
 * `sbx.files` paths (src/sandbox/parts.ts) against the contract-driven mock API, whose files routes keep the
 * service's rule: every files path is relative to `/workspace`, and an absolute one or a `.` or `..` segment is
 * answered with a 400. Each verb sends a path under `/workspace` relative to it, lists `/workspace` itself with no
 * path at all, and refuses a path outside `/workspace`, a dotted one, a control character, a backslash, an
 * over-long one and (outside `list`) `/workspace` itself, with `invalid_path` before any request.
 * Synthetic credentials only; no socket.
 */
import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { FutureAGIClient } from "../../futureagi-client";
import { Sandbox, SandboxError, ValidationError } from "../index";
import { SID, SandboxApi } from "../__fixtures__/openapi-mock";

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
/** A Future AGI host: hosted keys go only to one (or to loopback). */
const HOSTED = "https://sandbox-fixture.futureagi.com/omega/api";
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
  api = new SandboxApi(HOSTED);
});
afterEach(() => {
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

const connect = (): Promise<Sandbox> => client().sandboxes.connect(SID);
const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);
/** Every request but the one `connect` makes. */
const fileCalls = () => api.calls.filter((c) => c.operation.operationId !== "getWorkspaceSandbox");

/** Each verb with one path argument, called the way a user would; `move` once per side. */
type Verb = readonly [name: string, operation: string, run: (sbx: Sandbox, path: string, dir: string) => Promise<unknown>];
const VERBS: readonly Verb[] = [
  ["list", "sandboxes.files.list", (sbx, path) => sbx.files.list(path)],
  ["read", "sandboxes.files.read", (sbx, path) => sbx.files.read(path)],
  ["readRecord", "sandboxes.files.read", (sbx, path) => sbx.files.readRecord(path, { maxBytes: 10 })],
  ["write", "sandboxes.files.write", (sbx, path) => sbx.files.write(path, "hi")],
  ["upload", "sandboxes.files.upload", (sbx, path) => sbx.files.upload(path, new Uint8Array([1, 2]))],
  ["download", "sandboxes.files.download", (sbx, path) => sbx.files.download(path)],
  ["downloadTo", "sandboxes.files.download", (sbx, path, dir) => sbx.files.downloadTo(path, join(dir, "out.bin"))],
  ["remove", "sandboxes.files.remove", (sbx, path) => sbx.files.remove(path, { recursive: true })],
  ["move (source)", "sandboxes.files.rename", (sbx, path) => sbx.files.move(path, "b.txt")],
  ["move (destination)", "sandboxes.files.rename", (sbx, path) => sbx.files.move("a.txt", path)],
  ["makeDir", "sandboxes.files.makeDir", (sbx, path) => sbx.files.makeDir(path)],
];

const OUTSIDE = ["/etc/passwd", "/", "//", "/workspacex/a", "/tmp/workspace/a", "/Workspace/a"];
const DOTTED = ["../a", "a/../b", "a/..", "./a", "a/./b", "/workspace/../etc/passwd", "/workspace/./a", "/workspace/a/.."];
const UNSENDABLE = ["a\u0000b", "a\nb", "a\tb", "a\u007fb", "a\\b", "/workspace/a\rb", "a".repeat(4097), `/workspace/${"a".repeat(4097)}`];
/** `/workspace` itself: a folder `list` takes, and no file or folder for any other verb. */
const ROOT = [".", "./", "/workspace", "/workspace/", "//workspace//", ""];

async function withDir<R>(run: (dir: string) => Promise<R>): Promise<R> {
  const dir = await mkdtemp(join(tmpdir(), "sbx-files-paths-"));
  try {
    return await run(dir);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

describe("each verb sends its path relative to /workspace", () => {
  it("list sends a folder under /workspace relative to it, and lists /workspace itself with no path sent", async () => {
    const sbx = await connect();
    for (const path of ["/workspace/sub", "sub/", "//workspace//sub//lib/", "sub/lib", ...ROOT]) await sbx.files.list(path);
    await sbx.files.list();
    expect(fileCalls().map((c) => c.query.get("path"))).toEqual(["sub", "sub", "sub/lib", "sub/lib", null, null, null, null, null, null, null]);
    expect(fileCalls().every((c) => c.operation.operationId === "listWorkspaceSandboxFiles")).toBe(true);
  });

  it("read and readRecord send a file under /workspace relative to it", async () => {
    api.on("readWorkspaceSandboxFile", () => api.ok("readWorkspaceSandboxFile", { file: { path: "sub/a.txt", encoding: "utf8", content: "hi" } }));
    const sbx = await connect();
    expect(await sbx.files.read("/workspace/sub/a.txt")).toBe("hi");
    expect((await sbx.files.readRecord("/workspace/sub/a.txt", { maxBytes: 5 })).content).toBe("hi");
    await sbx.files.read("sub/a.txt");
    const reads = api.callsTo("readWorkspaceSandboxFile");
    expect(reads.map((c) => c.params.path)).toEqual(["sub/a.txt", "sub/a.txt", "sub/a.txt"]);
    expect(reads[1]!.query.get("maxBytes")).toBe("5");
  });

  it("write and upload send a file under /workspace relative to it; a name that starts with a dot is kept", async () => {
    const sbx = await connect();
    await sbx.files.write("/workspace/sub/.keep", "");
    await sbx.files.upload("/workspace/sub/data.bin", new Uint8Array([1, 2, 3]));
    expect(api.callsTo("writeWorkspaceSandboxFile").map((c) => [c.params.path, c.json])).toEqual([["sub/.keep", { content: "", encoding: "utf8" }]]);
    expect(api.callsTo("uploadWorkspaceSandboxFile").map((c) => c.params.path)).toEqual(["sub/data.bin"]);
  });

  it("download and downloadTo send a file under /workspace relative to it", async () => {
    const sbx = await connect();
    expect(Array.from(await sbx.files.download("/workspace/out/a.bin"))).toEqual([0, 1, 2, 255]);
    await withDir(async (dir) => {
      const target = join(dir, "a.bin");
      expect(await sbx.files.downloadTo("/workspace/out/a.bin", target)).toBe(target);
      expect(await readdir(dir)).toEqual(["a.bin"]);
    });
    expect(api.callsTo("downloadWorkspaceSandboxFile").map((c) => c.params.path)).toEqual(["out/a.bin", "out/a.bin"]);
  });

  it("remove, move and makeDir send their paths under /workspace relative to it", async () => {
    const sbx = await connect();
    await sbx.files.remove("/workspace/old", { recursive: true });
    await sbx.files.move("/workspace/a.txt", "/workspace/sub/b.txt");
    await sbx.files.move("a.txt", "sub//c.txt");
    await sbx.files.makeDir("/workspace/sub/new/");
    expect(api.callsTo("deleteWorkspaceSandboxPath").map((c) => [c.params.path, c.query.get("recursive")])).toEqual([["old", "true"]]);
    expect(api.callsTo("moveWorkspaceSandboxPath").map((c) => c.json)).toEqual([{ from: "a.txt", to: "sub/b.txt" }, { from: "a.txt", to: "sub/c.txt" }]);
    expect(api.callsTo("createWorkspaceSandboxFolder").map((c) => c.params.path)).toEqual(["sub/new"]);
  });

  it("a relative path is sent as given, with repeated and trailing slashes dropped", async () => {
    const sbx = await connect();
    await sbx.files.write("a//b/c.txt", "x");
    await sbx.files.write("workspace/notes.md", "x");
    await sbx.files.makeDir("dir/sub/");
    expect(api.callsTo("writeWorkspaceSandboxFile").map((c) => c.params.path)).toEqual(["a/b/c.txt", "workspace/notes.md"]);
    expect(api.callsTo("createWorkspaceSandboxFolder").map((c) => c.params.path)).toEqual(["dir/sub"]);
  });
});

describe("a path the files API would refuse or misplace is refused before any request", () => {
  it.each(VERBS)("%s refuses a path outside /workspace, a . or .. segment, a control character, a backslash and an over-long path", async (_name, operation, run) => {
    const sbx = await connect();
    await withDir(async (dir) => {
      for (const path of [...OUTSIDE, ...DOTTED, ...UNSENDABLE]) {
        const error = await failure(() => run(sbx, path, dir));
        expect([path, error]).toEqual([path, expect.any(SandboxError)]);
        expect(error).toMatchObject({ code: "invalid_path", operation });
        expect(error).not.toBeInstanceOf(ValidationError);
        expect((error as SandboxError).status).toBeUndefined();
      }
      expect(await readdir(dir)).toEqual([]);
    });
    expect(fileCalls()).toEqual([]);
  });

  it.each(VERBS.filter(([name]) => name !== "list"))("%s refuses /workspace itself, which names no file or folder", async (_name, operation, run) => {
    const sbx = await connect();
    await withDir(async (dir) => {
      for (const path of ROOT) {
        const error = await failure(() => run(sbx, path, dir));
        expect([path, error]).toEqual([path, expect.any(SandboxError)]);
        expect(error).toMatchObject({ code: "invalid_path", operation });
      }
    });
    expect(fileCalls()).toEqual([]);
  });

  it.each(VERBS)("%s returns a rejected promise for a refused path, never a synchronous throw", async (_name, _operation, run) => {
    const sbx = await connect();
    await withDir(async (dir) => {
      let returned: unknown;
      expect(() => {
        returned = run(sbx, "/etc/passwd", dir);
      }).not.toThrow();
      expect(returned).toBeInstanceOf(Promise);
      await expect(returned).rejects.toMatchObject({ code: "invalid_path" });
    });
    expect(fileCalls()).toEqual([]);
  });

  it("the message names the path and says what to pass instead, with a control character escaped", async () => {
    const sbx = await connect();
    const message = async (call: () => Promise<unknown>): Promise<string> => ((await failure(call)) as Error).message;
    const outside = await message(() => sbx.files.read("/etc/passwd"));
    expect(outside).toContain('path "/etc/passwd" is outside /workspace');
    expect(outside).toContain("relative to it");
    expect(await message(() => sbx.files.write("a/../b", "x"))).toContain('path "a/../b" has a "." or ".." segment');
    const control = await message(() => sbx.files.makeDir("a\nb"));
    expect(control).toContain('"a\\nb"');
    expect(control.includes("\n")).toBe(false);
    const long = await message(() => sbx.files.list("a".repeat(5000)));
    expect(long).toContain("5000 characters");
    expect(long.length).toBeLessThan(300);
    expect(await message(() => sbx.files.remove("/workspace"))).toContain("names no file or folder under /workspace");
    expect(await message(() => sbx.files.move("../a", "b"))).toMatch(/^source "\.\.\/a"/u);
    expect(await message(() => sbx.files.move("a", "/tmp/b"))).toMatch(/^destination "\/tmp\/b" is outside \/workspace/u);
    expect(fileCalls()).toEqual([]);
  });
});

describe("the mock files routes refuse what the service refuses", () => {
  it("answers an absolute or dotted list path, or move path, with a 400, before any scripted answer", async () => {
    api.on("listWorkspaceSandboxFiles", () => api.ok("listWorkspaceSandboxFiles"));
    const files = client().sandboxes.files;
    for (const path of ["/workspace/sub", ".", "a/../b", "/etc"]) {
      const error = await failure(() => files.list(SID, { path }));
      expect([path, error]).toEqual([path, expect.any(ValidationError)]);
      expect(error).toMatchObject({ status: 400, code: "validation" });
      expect((error as Error).message).toContain("path must");
    }
    for (const body of [{ from: "/workspace/a.txt", to: "b.txt" }, { from: "a.txt", to: "./b.txt" }]) {
      expect(await failure(() => files.rename(SID, { body }))).toMatchObject({ status: 400, code: "validation" });
    }
    expect((await files.list(SID, { path: "sub" })).entries).toEqual([]);
    expect((await files.list(SID)).entries).toEqual([]);
    expect((await files.rename(SID, { body: { from: "a.txt", to: "sub/b.txt" } })).schemaVersion).toBeDefined();
    expect(api.callsTo("listWorkspaceSandboxFiles")).toHaveLength(6);
    expect(api.callsTo("moveWorkspaceSandboxPath")).toHaveLength(3);
  });
});
