/**
 * `client.sandboxes.files` paths (src/platform/resources/sandboxes.ts) against the contract-driven mock API, whose
 * files routes answer an absolute or dotted path with a 400, as the service does. The layer takes a path the way
 * `sbx.files` does: relative to `/workspace`, or absolute under it (`/workspace/a.txt` is sent as `a.txt`);
 * `/workspace` itself is a folder only `list` takes, and for it no path is sent. A path outside `/workspace`, one
 * with a `.` or `..` segment, a backslash or a control character, and one over 4096 characters is refused with
 * `invalid_path` before any request. Synthetic credentials only; no socket.
 */
import { FutureAGIClient } from "../../futureagi-client";
import { SandboxError, ValidationError } from "../../sandbox";
import { SID, SandboxApi } from "../../sandbox/__fixtures__/openapi-mock";
import type { SandboxFiles } from "../resources/sandboxes";

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
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

function files(): SandboxFiles {
  const c = new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, platformBaseUrl: api.base, fetch: api.fetch });
  Object.assign(c._platform.shared, { sleep: async () => undefined });
  return c.sandboxes.files;
}

const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);

/** Each method with one path argument, called the way a user would. */
type Verb = readonly [name: string, operation: string, operationId: string, run: (f: SandboxFiles, path: string) => PromiseLike<unknown>];
const VERBS: readonly Verb[] = [
  ["write", "sandboxes.files.write", "writeWorkspaceSandboxFile", (f, path) => f.write(SID, path, { body: { content: "hi", encoding: "utf8" } })],
  ["read", "sandboxes.files.read", "readWorkspaceSandboxFile", (f, path) => f.read(SID, path, { maxBytes: 10 })],
  ["remove", "sandboxes.files.remove", "deleteWorkspaceSandboxPath", (f, path) => f.remove(SID, path, { recursive: true })],
  ["makeDir", "sandboxes.files.makeDir", "createWorkspaceSandboxFolder", (f, path) => f.makeDir(SID, path)],
  ["download", "sandboxes.files.download", "downloadWorkspaceSandboxFile", (f, path) => f.download(SID, path)],
  ["upload", "sandboxes.files.upload", "uploadWorkspaceSandboxFile", (f, path) => f.upload(SID, path, { body: new Uint8Array([1, 2]) })],
  ["list", "sandboxes.files.list", "listWorkspaceSandboxFiles", (f, path) => f.list(SID, { path })],
];

/** The paths one operation sent: the list route's `path` query (null when none), else its `{path}` parameter. */
const sent = (operationId: string): (string | null)[] =>
  api.callsTo(operationId).map((c) => (operationId === "listWorkspaceSandboxFiles" ? c.query.get("path") : c.params.path));

const OUTSIDE = ["/etc/passwd", "/tmp/a.txt", "/", "/workspacex/a.txt", "/tmp/workspace/a.txt"];
const DOTTED = ["src/../a.txt", "../a.txt", "./a.txt", "a/..", "/workspace/../etc/passwd", "/workspace/./a.txt", "/workspace/."];
const UNSENDABLE = ["a\\b.txt", "a\u0000b", "a\nb", "/workspace/a\u007fb", "a".repeat(4097), `/workspace/${"a".repeat(4097)}`];
/** `/workspace` itself: a folder `list` takes, and no file or folder for any other method. */
const ROOT = ["/workspace", "/workspace/", "//workspace//", ".", "./", ""];

describe("client.sandboxes.files sends each path relative to /workspace", () => {
  it.each(VERBS)("%s sends /workspace/a.txt as a.txt, and a relative path as given", async (_name, _operation, operationId, run) => {
    const f = files();
    for (const path of ["/workspace/a.txt", "//workspace//sub//b.txt/", "sub/c.txt", "workspace/notes.md", "dir/a b.txt"]) await run(f, path);
    expect(sent(operationId)).toEqual(["a.txt", "sub/b.txt", "sub/c.txt", "workspace/notes.md", "dir/a b.txt"]);
    expect(api.calls).toHaveLength(5);
  });

  it("list takes /workspace itself and sends no path for it, as with no path at all", async () => {
    const f = files();
    for (const path of ROOT) await f.list(SID, { path });
    await f.list(SID);
    expect(sent("listWorkspaceSandboxFiles")).toEqual([null, null, null, null, null, null, null]);
    expect(api.calls).toHaveLength(7);
  });

  it("an encoded name is sent as that literal name, one segment at a time", async () => {
    await files().write(SID, "/workspace/%2e%2e/a b.txt", { body: { content: "x", encoding: "utf8" } });
    expect(api.calls[0]!.request.url).toBe(`${api.base}/workspace/sandboxes/${SID}/files/%252e%252e/a%20b.txt`);
    expect(sent("writeWorkspaceSandboxFile")).toEqual(["%2e%2e/a b.txt"]);
  });
});

describe("client.sandboxes.files refuses a path the files API would refuse or misplace, before any request", () => {
  it.each(VERBS)("%s refuses a path outside /workspace, a . or .. segment, a backslash, a control character and an over-long path", async (_name, operation, _id, run) => {
    const f = files();
    for (const path of [...OUTSIDE, ...DOTTED, ...UNSENDABLE]) {
      const error = await failure(() => run(f, path));
      expect([path, error]).toEqual([path, expect.any(SandboxError)]);
      expect(error).toMatchObject({ code: "invalid_path", operation });
      expect(error).not.toBeInstanceOf(ValidationError);
      expect((error as SandboxError).status).toBeUndefined();
    }
    expect(api.calls).toEqual([]);
  });

  it.each(VERBS.filter(([name]) => name !== "list"))("%s refuses /workspace itself, which names no file or folder", async (_name, operation, _id, run) => {
    const f = files();
    for (const path of ROOT) {
      const error = await failure(() => run(f, path));
      expect([path, error]).toEqual([path, expect.any(SandboxError)]);
      expect(error).toMatchObject({ code: "invalid_path", operation });
    }
    expect(api.calls).toEqual([]);
  });

  it.each(VERBS)("%s returns a rejected call for a refused path, never a synchronous throw", async (_name, _operation, _id, run) => {
    let returned: unknown;
    expect(() => {
      returned = run(files(), "/etc/passwd");
    }).not.toThrow();
    await expect(returned).rejects.toMatchObject({ code: "invalid_path" });
    expect(api.calls).toEqual([]);
  });

  it("the message names the path as given, cut to 200 characters", async () => {
    const f = files();
    const message = async (call: () => PromiseLike<unknown>): Promise<string> => ((await failure(call)) as Error).message;
    expect(await message(() => f.write(SID, "/tmp/a.txt", { body: { content: "x", encoding: "utf8" } }))).toContain('path "/tmp/a.txt" is outside /workspace');
    expect(await message(() => f.makeDir(SID, "src/../a"))).toContain('path "src/../a" has a "." or ".." segment');
    expect(await message(() => f.remove(SID, "/workspace"))).toContain('path "/workspace" names no file or folder under /workspace');
    expect(await message(() => f.read(SID, "."))).toContain('path "." names no file or folder under /workspace');
    const long = await message(() => f.list(SID, { path: `/tmp/${"a".repeat(5000)}` }));
    expect(long).toContain(`path "/tmp/${"a".repeat(195)}..." is outside /workspace`);
    expect(long.length).toBeLessThan(500);
    expect(api.calls).toEqual([]);
  });
});
