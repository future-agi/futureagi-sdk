/**
 * `sbx.files`, `sbx.snapshots` and `sbx.networkPolicy`. Each method calls `client.sandboxes` once (the
 * network policy's `set` reads the current revision first when no `ifMatch` is given) and throws sandbox errors.
 * Nothing that changes a file is retried. A file path the files API would refuse or misplace is refused before
 * anything is sent (see `Files`).
 */

import { v4 as uuidv4 } from "uuid";

import type * as T from "../generated/platform/types.gen";
import type { Sandboxes, UploadBody } from "../platform/resources/sandboxes";
import { mapped, SandboxError } from "./errors";
import type { Sandbox } from "./sandbox";
import type { DownloadOptions } from "./wire";

/** One entry of a folder listing. */
export type FileEntry = T.ListWorkspaceSandboxFilesResponse["entries"][number];
/** A snapshot record. */
export type SnapshotInfo = T.SnapshotWorkspaceSandboxResponse["snapshot"];
/** Desired versus applied egress policy. */
export type NetworkPolicyState = T.GetWorkspaceSandboxNetworkPolicyResponse["policy"];
/** `sbx.networkPolicy.get()`: the policy plus its `etag` (the quoted desired revision, `"3"`), which is the
 * `ifMatch` of a guarded `set`. */
export type NetworkPolicyRecord = NetworkPolicyState & { readonly etag: string };

const CHUNK = 0x8000;

function toBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i += CHUNK) binary += String.fromCharCode(...Array.from(bytes.subarray(i, i + CHUNK)));
  return btoa(binary);
}

function fromBase64(text: string): Uint8Array {
  const binary = atob(text);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
  return out;
}

type Bound = { readonly id: string };

/** The sandbox folder the files API reaches, `/workspace`; it takes every path relative to it. */
const WORKSPACE_NAME = "workspace";
const WORKSPACE = `/${WORKSPACE_NAME}`;
/** The longest path the files API takes, in characters. */
const MAX_PATH_CHARS = 4096;

/** A control character (U+0000 to U+001F, or U+007F) anywhere in `text`. */
function hasControl(text: string): boolean {
  for (let i = 0; i < text.length; i += 1) {
    const code = text.charCodeAt(i);
    if (code < 0x20 || code === 0x7f) return true;
  }
  return false;
}

function invalidPath(message: string, operation: string): SandboxError {
  return new SandboxError(message, { code: "invalid_path", operation });
}

/** `path` as a refusal shows it: as given, JSON-quoted (so a control character is escaped) and cut to 200
 * characters with an ellipsis. */
export function shownPath(path: string): string {
  return JSON.stringify(path.length > 200 ? `${path.slice(0, 200)}...` : path);
}

/** Whether `path` is absolute and outside `/workspace` (`/tmp/a`, `/`, `/workspacex/a`). `/workspace/../a` is not:
 * it is under `/workspace` with a `..` segment, which `filesPath` refuses as such (nothing is folded). */
export function outsideWorkspace(path: string): boolean {
  return path.startsWith("/") && path.split("/").find((part) => part !== "") !== WORKSPACE_NAME;
}

/**
 * `path` as the files API takes it: relative to `/workspace`, so `/workspace/src/a.ts` is sent as `src/a.ts` (sent
 * as it is, an absolute path is refused, or lands under `/workspace` a second time as `/workspace/workspace/src/a.ts`);
 * repeated and trailing slashes are dropped. `""` and `.` stand for `/workspace` itself, which only a listing
 * (`root`) takes; `""` is returned for it. Anything the API would refuse is refused here with `invalid_path`, before
 * anything is sent, and the message names the path as given. `sbx.files` and `client.sandboxes.files` both take
 * their paths through it.
 */
export function filesPath(path: unknown, what: string, operation: string, root = false): string {
  if (typeof path !== "string") throw invalidPath(`${what} must be a path string, not ${typeof path}`, operation);
  const shown = shownPath(path);
  if (hasControl(path) || path.includes("\\")) {
    throw invalidPath(`${what} ${shown} contains a control character or a backslash, which the files API refuses`, operation);
  }
  let parts = path.split("/").filter((part) => part !== "");
  if (path.startsWith("/")) {
    if (outsideWorkspace(path)) {
      throw invalidPath(
        `${what} ${shown} is outside ${WORKSPACE}: the sandbox's file calls reach only ${WORKSPACE} and what is under ` +
          `it, so pass a path under ${WORKSPACE} (or one relative to it); read anything else with a command such as cat`,
        operation,
      );
    }
    parts = parts.slice(1);
  } else if (parts.length === 1 && parts[0] === ".") {
    parts = [];
  }
  if (parts.some((part) => part === "." || part === "..")) {
    throw invalidPath(
      `${what} ${shown} has a "." or ".." segment, which the files API refuses: pass the path under ${WORKSPACE} ` +
        `without them (absolute, or relative to ${WORKSPACE})`,
      operation,
    );
  }
  const relative = parts.join("/");
  if (relative === "" && !root) {
    throw invalidPath(`${what} ${shown} names no file or folder under ${WORKSPACE} (only a listing takes ${WORKSPACE} itself)`, operation);
  }
  if (relative.length > MAX_PATH_CHARS) {
    throw invalidPath(`${what} is ${relative.length} characters long; the files API takes at most ${MAX_PATH_CHARS}`, operation);
  }
  return relative;
}

/**
 * `sbx.files`: files and folders under the sandbox's `/workspace`, the only folder the files API reaches. A path is
 * absolute under `/workspace` (`/workspace/src/a.ts`) or relative to it (`src/a.ts`); either is sent relative to
 * `/workspace`, as the files API takes it. `/workspace` itself (or `.`) is a path only for `list`. A path outside
 * `/workspace`, one with a `.` or `..` segment, a backslash or a control character, and one over 4096 characters
 * is refused before anything is sent: a `SandboxError` with code `invalid_path`. Read or copy anything outside
 * `/workspace` with a command.
 */
export class Files {
  readonly #api: Sandboxes;
  readonly #sandbox: Bound;

  /** @internal Built by `Sandbox`. */
  constructor(api: Sandboxes, sandbox: Bound) {
    this.#api = api;
    this.#sandbox = sandbox;
  }

  /** The entries of a folder (default: `/workspace` itself, which `.` and `/workspace` also name). */
  async list(path = "."): Promise<FileEntry[]> {
    const folder = filesPath(path, "path", "sandboxes.files.list", true);
    // the files API lists /workspace itself when no path is sent (it refuses ".")
    const response = await mapped(() => this.#api.files.list(this.#sandbox.id, folder === "" ? {} : { path: folder }));
    return response.entries;
  }

  /** A file's content, bounded by `maxBytes`: a string for text, bytes for anything else. Use `readRecord`
   * when the size matters: it also says whether the content was cut (`truncated`). */
  async read(path: string, options: { maxBytes?: number } = {}): Promise<string | Uint8Array> {
    const file = await this.readRecord(path, options);
    return file.encoding === "base64" ? fromBase64(file.content) : file.content;
  }

  /** The read as the server sent it: `content` (the text when `encoding` is `utf8`, else base64), `bytes`, and
   * `truncated` when the content stops before the end of the file (at `maxBytes` or the workspace's
   * `caps.files.maxReadBytes`). One call, like `read`. */
  async readRecord(path: string, options: { maxBytes?: number } = {}): Promise<T.ReadWorkspaceSandboxFileResponse["file"]> {
    const file = filesPath(path, "path", "sandboxes.files.read");
    const response = await mapped(() => this.#api.files.read(this.#sandbox.id, file, options));
    return response.file;
  }

  /** Write a small text or binary file (audited; up to the JSON body limit). Never retried. */
  async write(path: string, data: string | Uint8Array | ArrayBuffer): Promise<T.WriteWorkspaceSandboxFileResponse> {
    const file = filesPath(path, "path", "sandboxes.files.write");
    const body: T.WriteWorkspaceSandboxFileRequest =
      typeof data === "string"
        ? { content: data, encoding: "utf8" }
        : { content: toBase64(data instanceof ArrayBuffer ? new Uint8Array(data) : data), encoding: "base64" };
    return mapped(() => this.#api.files.write(this.#sandbox.id, file, { body }));
  }

  /** Upload raw bytes, a Blob (`await fs.openAsBlob(file)`) or text; the folder must exist. Never retried. */
  async upload(path: string, data: UploadBody): Promise<T.UploadWorkspaceSandboxFileResponse> {
    const file = filesPath(path, "path", "sandboxes.files.upload");
    return mapped(() => this.#api.files.upload(this.#sandbox.id, file, { body: data }));
  }

  /** A file's raw bytes, up to `maxBytes` (default 64 MiB, the upload limit): a larger file throws
   * `PayloadTooLargeError` (code `download_too_large`, `limitBytes`) and nothing is kept. */
  async download(path: string, options: { readonly maxBytes?: number } = {}): Promise<Uint8Array> {
    const file = filesPath(path, "path", "sandboxes.files.download");
    const call: DownloadOptions = options.maxBytes !== undefined ? { maxBytes: options.maxBytes } : {};
    return mapped(() => this.#api.files.download(this.#sandbox.id, file, call));
  }

  /** Download to `localPath`, up to `maxBytes` as `download`: written to a temporary file next to it, renamed only
   * once complete (Node.js). On any failure, including a file over the limit or a refused path, no file is left
   * behind. */
  async downloadTo(path: string, localPath: string, options: { readonly maxBytes?: number } = {}): Promise<string> {
    const data = await this.download(path, options);
    const fs = await import("node:fs/promises");
    const partial = `${localPath}.${uuidv4()}.partial`;
    try {
      await fs.writeFile(partial, data, { flag: "wx" });
      await fs.rename(partial, localPath);
    } catch (error) {
      await fs.rm(partial, { force: true }).catch(() => undefined);
      throw error;
    }
    return localPath;
  }

  /** Delete a file, or a folder with `recursive` (never `/workspace` itself). Never retried. */
  async remove(path: string, options: { recursive?: boolean } = {}): Promise<T.DeleteWorkspaceSandboxPathResponse> {
    const target = filesPath(path, "path", "sandboxes.files.remove");
    return mapped(() => this.#api.files.remove(this.#sandbox.id, target, options));
  }

  /** Move or rename a file or folder; both paths follow the rules above. Never retried. */
  async move(source: string, destination: string): Promise<T.MoveWorkspaceSandboxPathResponse> {
    const from = filesPath(source, "source", "sandboxes.files.rename");
    const to = filesPath(destination, "destination", "sandboxes.files.rename");
    return mapped(() => this.#api.files.rename(this.#sandbox.id, { body: { from, to } }));
  }

  /** Create a folder. Never retried. */
  async makeDir(path: string): Promise<T.CreateWorkspaceSandboxFolderResponse> {
    const folder = filesPath(path, "path", "sandboxes.files.makeDir");
    return mapped(() => this.#api.files.makeDir(this.#sandbox.id, folder));
  }
}

/** `sbx.snapshots`: snapshots of the sandbox's files. */
export class Snapshots {
  readonly #api: Sandboxes;
  readonly #sandbox: Bound;

  /** @internal Built by `Sandbox`. */
  constructor(api: Sandboxes, sandbox: Bound) {
    this.#api = api;
    this.#sandbox = sandbox;
  }

  /** Snapshot the files now. Never retried. */
  async create(): Promise<SnapshotInfo> {
    const response = await mapped(() => this.#api.snapshots.create(this.#sandbox.id));
    return response.snapshot;
  }

  /** The sandbox's snapshots. */
  async list(): Promise<SnapshotInfo[]> {
    const response = await mapped(() => this.#api.snapshots.list(this.#sandbox.id));
    return response.snapshots;
  }

  /** Restore a snapshot as a NEW sandbox; this one is unchanged. Never retried. */
  restore(snapshotId: string, options: T.RestoreWorkspaceSandboxSnapshotRequest = {}): Promise<Sandbox> {
    return mapped(() => this.#api.snapshots.restore(this.#sandbox.id, snapshotId, { body: options }));
  }
}

/** `sbx.networkPolicy`: the sandbox's egress policy. */
export class NetworkPolicy {
  readonly #api: Sandboxes;
  readonly #sandbox: Bound;

  /** @internal Built by `Sandbox`. */
  constructor(api: Sandboxes, sandbox: Bound) {
    this.#api = api;
    this.#sandbox = sandbox;
  }

  /** Desired versus applied policy, with its `etag` (the response's `ETag` header; the quoted desired revision
   * if a proxy dropped the header). */
  async get(): Promise<NetworkPolicyRecord> {
    const { data, meta } = await mapped(() => this.#api.networkPolicy.get(this.#sandbox.id).withResponse());
    return { ...data.policy, etag: meta.headers.etag ?? `"${data.policy.desiredRevision}"` };
  }

  /** Replace the policy. `ifMatch` (an `etag` from `get()`) guards against a concurrent change; without it the
   * current policy is read first and its `etag` sent, so the replacement applies to the revision just read.
   * A stale revision is a `ConflictError` (status 412, code `network_policy_revision_mismatch`); nothing here
   * retries it or reads again. Never retried. */
  async set(policy: T.PutWorkspaceSandboxNetworkPolicyRequest, options: { ifMatch?: string } = {}): Promise<T.PutWorkspaceSandboxNetworkPolicyResponse> {
    const ifMatch = options.ifMatch ?? (await this.get()).etag;
    return mapped(() => this.#api.networkPolicy.update(this.#sandbox.id, { body: policy, ifMatch }));
  }
}
