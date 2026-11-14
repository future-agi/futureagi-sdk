// `client.sandboxes`: one method per wrapped sandbox operation of the pinned customer contract, named by the
// operation's `x-omega-sdk` method (`getInfo`, `kill`, `files.makeDir`, `networkPolicy.update`,
// `commands.run`, ...), each called by its SDK name through the shared platform executor
// (src/_core/platform-base.ts). Errors are the sandbox classes of src/sandbox/errors.ts (`SandboxError` and its
// status classes, each a subclass of the shared platform class the executor would throw, so existing handlers
// still catch them), the same as the `Sandbox` handle throws. The handle (src/sandbox) sits on top of this
// layer and never builds a request itself. `connect` is the contract's handle alias of `getInfo`.
//
// Sandbox rules on top of the executor (src/sandbox/wire.ts):
// - there is no default host: a client given neither `baseUrl` / `platformBaseUrl` nor `FI_BASE_URL` /
//   `FI_PLATFORM_BASE_URL` is refused before anything is sent (`missing_base_url`);
// - plain HTTP to anything but loopback is refused before a request is built (`insecure_sandbox_origin`), in
//   both credential modes and whatever `allowInsecureHttp` says;
// - a self-hosted origin (Bearer token) that is not loopback, a Future AGI host included, needs the
//   constructor-only `allowCustomBaseUrl: true` (OpenAPI servers[1]); `FI_ALLOW_CUSTOM_PLATFORM_URL` and
//   `allowCustomPlatformUrl` do not stand in for it;
// - a files path is taken by the rule `sbx.files` keeps (src/sandbox/parts.ts): relative to `/workspace`, so an
//   absolute path under it is sent relative to it, and a path the files API would refuse or misplace is refused
//   with `invalid_path` before anything is sent;
// - a download is read up to `maxBytes` (default 64 MiB, the upload limit); a larger file throws
//   `PayloadTooLargeError` (code `download_too_large`) and nothing is kept;
// - every call the contract marks non-idempotent is sent once, with no retry at all (not on a 429, not after a
//   failure before sending): create, hibernate, resume, snapshots.create, snapshots.restore, files.rename,
//   files.upload, files.write, files.makeDir, files.remove and networkPolicy.update. `update` and
//   `commands.cancel` keep the executor's rule for a POST or PATCH (retried only on a 429 or a failure before
//   sending, never after the request may have reached the server); reads and `kill` keep its retries;
// - commands.run is a stream and is never retried; closing an `ExecStream` closes the connection, which
//   cancels the command (the contract's cancel-on-disconnect);
// - a redirect error names no target host;
// - sandbox settings are read-only here: they are changed in the Console, from an owner's or admin's
//   signed-in session (`settings.update` is human-only and not wrapped).

import type * as T from "../../generated/platform/types.gen";
import type { Opened } from "../../_core/platform-base";
import { APIPromise } from "../../_core/raw";
import { filesPath } from "../../sandbox/parts";
import { Sandbox } from "../../sandbox/sandbox";
import {
  type Bound,
  bytes,
  call,
  type DownloadOptions,
  ExecStream,
  failure,
  type Host,
  type SandboxCallOptions,
  sandboxCore,
  type UploadBody,
} from "../../sandbox/wire";

export {
  type DownloadOptions,
  ExecStream,
  type ExecFrame,
  type SandboxCallOptions,
  type UnknownExecFrame,
  type UploadBody,
} from "../../sandbox/wire";

/**
 * `send` with `path` as the files API takes it, by the rule `sbx.files` keeps (src/sandbox/parts.ts `filesPath`):
 * relative to `/workspace`, so an absolute path under it is sent relative to it. A path the files API would refuse
 * or misplace is refused inside the returned call (a `SandboxError` with code `invalid_path`), so nothing is sent and
 * nothing throws synchronously. `root` lets the path name `/workspace` itself, given to `send` as `""`.
 */
function inWorkspace<R>(path: unknown, operation: string, send: (relative: string) => APIPromise<R>, root = false): APIPromise<R> {
  return new APIPromise(async () => {
    const { data, meta } = await send(filesPath(path, "path", operation, root)).withResponse();
    return { data, meta };
  });
}

/**
 * `client.sandboxes.files`: files and folders by path inside a sandbox's `/workspace`, the only folder the files API
 * reaches. A path is relative to `/workspace` (`src/a.ts`) or absolute under it (`/workspace/src/a.ts`, sent as
 * `src/a.ts`); `/workspace` itself (or `.`) is a path only for `list`. A path outside `/workspace`, one with a `.` or
 * `..` segment, a backslash or a control character, and one over 4096 characters is refused before anything is
 * sent: a `SandboxError` with code `invalid_path`, as `sbx.files` refuses it. `rename` sends its body as given.
 */
export class SandboxFiles {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** List a folder's entries (`path` defaults to `/workspace` itself, which `.` and `/workspace` also name: for it
   * no path is sent). Returns the complete response envelope. */
  list(sandboxId: string, options: SandboxCallOptions & { path?: string } = {}): APIPromise<T.ListWorkspaceSandboxFilesResponse> {
    const { path, ...rest } = options;
    const name = "sandboxes.files.list";
    // the files API lists /workspace itself when no path is sent (it refuses ".")
    const send = (folder = ""): APIPromise<T.ListWorkspaceSandboxFilesResponse> =>
      call(this.#bound, name, { path: { id: sandboxId }, query: { path: folder === "" ? undefined : folder } }, rest);
    return path === undefined ? send() : inWorkspace(path, name, send, true);
  }
  /** Read one file, bounded by `maxBytes`; `file.encoding` says utf8 or base64. Returns the complete response envelope. */
  read(sandboxId: string, path: string, options: SandboxCallOptions & { maxBytes?: number } = {}): APIPromise<T.ReadWorkspaceSandboxFileResponse> {
    const { maxBytes, ...rest } = options;
    const name = "sandboxes.files.read";
    return inWorkspace(path, name, (file: string) =>
      call<T.ReadWorkspaceSandboxFileResponse>(this.#bound, name, { path: { id: sandboxId, path: file }, query: { maxBytes } }, rest));
  }
  /** Write a small text or base64 file (audited). Sent once, never retried. Returns the complete response envelope. */
  write(sandboxId: string, path: string, options: SandboxCallOptions & { body: T.WriteWorkspaceSandboxFileRequest }): APIPromise<T.WriteWorkspaceSandboxFileResponse> {
    const { body, ...rest } = options;
    const name = "sandboxes.files.write";
    return inWorkspace(path, name, (file: string) =>
      call<T.WriteWorkspaceSandboxFileResponse>(this.#bound, name, { path: { id: sandboxId, path: file }, body }, rest, true));
  }
  /** Delete a file, or a folder with `recursive` (never `/workspace` itself). Sent once, never retried. Returns the
   * complete response envelope. */
  remove(sandboxId: string, path: string, options: SandboxCallOptions & { recursive?: boolean } = {}): APIPromise<T.DeleteWorkspaceSandboxPathResponse> {
    const { recursive, ...rest } = options;
    const name = "sandboxes.files.remove";
    return inWorkspace(path, name, (file: string) =>
      call<T.DeleteWorkspaceSandboxPathResponse>(this.#bound, name, { path: { id: sandboxId, path: file }, query: { recursive } }, rest, true));
  }
  /** A file's raw bytes, up to `maxBytes` (default 64 MiB, the upload limit): a larger file throws
   * `PayloadTooLargeError` (code `download_too_large`) and nothing is kept. */
  download(sandboxId: string, path: string, options: DownloadOptions = {}): APIPromise<Uint8Array> {
    const name = "sandboxes.files.download";
    return inWorkspace(path, name, (file: string) => bytes(this.#bound, name, { path: { id: sandboxId, path: file } }, options));
  }
  /** Upload raw bytes; the target is replaced only once every byte arrived, and its folder must exist. Sent once, never retried. */
  upload(sandboxId: string, path: string, options: SandboxCallOptions & { body: UploadBody }): APIPromise<T.UploadWorkspaceSandboxFileResponse> {
    const { body, ...rest } = options;
    const raw = body instanceof ArrayBuffer ? new Uint8Array(body) : body;
    const name = "sandboxes.files.upload";
    return inWorkspace(path, name, (file: string) =>
      call<T.UploadWorkspaceSandboxFileResponse>(this.#bound, name, { path: { id: sandboxId, path: file }, body: raw }, rest, true));
  }
  /** Move or rename a file or folder (`body.from` to `body.to`, each relative to `/workspace`; sent as given). Sent
   * once, never retried. Returns the complete response envelope. */
  rename(sandboxId: string, options: SandboxCallOptions & { body: T.MoveWorkspaceSandboxPathRequest }): APIPromise<T.MoveWorkspaceSandboxPathResponse> {
    const { body, ...rest } = options;
    return call(this.#bound, "sandboxes.files.rename", { path: { id: sandboxId }, body }, rest, true);
  }
  /** Create a folder and its parents. Sent once, never retried. Returns the complete response envelope. */
  makeDir(sandboxId: string, path: string, options: SandboxCallOptions = {}): APIPromise<T.CreateWorkspaceSandboxFolderResponse> {
    const name = "sandboxes.files.makeDir";
    return inWorkspace(path, name, (folder: string) =>
      call<T.CreateWorkspaceSandboxFolderResponse>(this.#bound, name, { path: { id: sandboxId, path: folder } }, options, true));
  }
}

/** `client.sandboxes.snapshots`: file snapshots, restored as new sandboxes. */
export class SandboxSnapshots {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** List a sandbox's snapshots. Returns the complete response envelope. */
  list(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.ListWorkspaceSandboxSnapshotsResponse> {
    return call(this.#bound, "sandboxes.snapshots.list", { path: { id: sandboxId } }, options);
  }
  /** Snapshot a sandbox's files. Sent once, never retried. Returns the complete response envelope. */
  create(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.SnapshotWorkspaceSandboxResponse> {
    return call(this.#bound, "sandboxes.snapshots.create", { path: { id: sandboxId } }, options, true);
  }
  /** Restore a snapshot as a NEW sandbox; the source is unchanged. Sent once, never retried. */
  async restore(sandboxId: string, snapshotId: string, options: SandboxCallOptions & { body?: T.RestoreWorkspaceSandboxSnapshotRequest } = {}): Promise<Sandbox> {
    const { body = {}, ...rest } = options;
    const response = await call<T.RestoreWorkspaceSandboxSnapshotResponse>(
      this.#bound, "sandboxes.snapshots.restore", { path: { id: sandboxId, snapshotId }, body }, rest, true,
    );
    return new Sandbox(Sandboxes._bound(this.#bound), response.sandbox);
  }
}

/** `client.sandboxes.settings`: the workspace's sandbox settings, read-only. Sandbox settings are changed in the
 * Console, from an owner's or admin's signed-in session; the SDK never changes them. */
export class SandboxSettings {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** Settings, caps, templates and sizes. Returns the complete response envelope. */
  get(options: SandboxCallOptions = {}): APIPromise<T.GetWorkspaceSandboxSettingsResponse> {
    return call(this.#bound, "sandboxes.settings.get", {}, options);
  }
}

/** `client.sandboxes.networkPolicy`: a sandbox's egress policy. */
export class SandboxNetworkPolicy {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** Desired and applied policy; the response's ETag (`.withResponse()`, `meta.headers.etag`) is the `ifMatch`
   * for `update`. Returns the complete response envelope. */
  get(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.GetWorkspaceSandboxNetworkPolicyResponse> {
    return call(this.#bound, "sandboxes.networkPolicy.get", { path: { id: sandboxId } }, options);
  }
  /** Replace the policy whole, guarded by `ifMatch` (the quoted revision, `"3"`). A stale revision is a 412
   * (`network_policy_revision_mismatch`). Sent once, never retried. */
  update(sandboxId: string, options: SandboxCallOptions & { body: T.PutWorkspaceSandboxNetworkPolicyRequest; ifMatch: string }): APIPromise<T.PutWorkspaceSandboxNetworkPolicyResponse> {
    const { body, ifMatch, ...rest } = options;
    return call(this.#bound, "sandboxes.networkPolicy.update", { path: { id: sandboxId }, body }, { ...rest, headers: { ...rest.headers, "If-Match": ifMatch } }, true);
  }
}

/** `client.sandboxes.activity`: a sandbox's audited activity. */
export class SandboxActivity {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** The sandbox's audited activity, newest first. Returns the complete response envelope. */
  list(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.ListWorkspaceSandboxActivityResponse> {
    return call(this.#bound, "sandboxes.activity.list", { path: { id: sandboxId } }, options);
  }
}

/** `client.sandboxes.commands`: run a command as a stream, or cancel one. */
export class SandboxCommands {
  readonly #bound: Bound;
  /** @internal Built by `client.sandboxes`. */
  constructor(bound: Bound) { this.#bound = bound; }
  /** Run a command; resolves once the stream is open (an HTTP refusal throws here). Never retried. */
  async run(sandboxId: string, options: SandboxCallOptions & { body: T.ExecInWorkspaceSandboxRequest }): Promise<ExecStream> {
    const { body, signal, ...rest } = options;
    const name = "sandboxes.commands.run";
    const core = sandboxCore(this.#bound, name);
    const controller = new AbortController();
    const forward = (): void => controller.abort(signal?.reason);
    if (signal?.aborted === true) forward();
    signal?.addEventListener("abort", forward, { once: true });
    const release = (): void => signal?.removeEventListener("abort", forward);
    let opened: Opened;
    try {
      opened = await core.openStream(name, { path: { id: sandboxId }, body }, { ...rest, signal: controller.signal });
    } catch (error) {
      release();
      throw failure(error);
    }
    return new ExecStream(opened, core, name, controller, release);
  }
  /** Cancel a running command by its exec id (retried only on a 429 or a failure before sending). Returns the
   * complete response envelope. */
  cancel(sandboxId: string, execId: string, options: SandboxCallOptions = {}): APIPromise<T.CancelWorkspaceSandboxExecResponse> {
    return call(this.#bound, "sandboxes.commands.cancel", { path: { id: sandboxId, execId } }, options);
  }
}

/** Hosted sandboxes in the selected workspace; construction sends no requests. */
export class Sandboxes {
  readonly #bound: Bound;
  /**
   * Bind a client without resolving credentials or opening a connection. `allowCustomBaseUrl` is the
   * `FutureAGIClient` constructor's opt-in for a self-hosted origin that is not loopback; `baseUrlGiven` says the
   * client was given a base URL (`baseUrl` or `FI_BASE_URL`), so an origin derived from it is a chosen host.
   */
  constructor(client: Host, options: { readonly allowCustomBaseUrl?: boolean; readonly baseUrlGiven?: boolean } = {}) {
    this.#bound = { host: client, allowCustomBaseUrl: options.allowCustomBaseUrl === true, baseUrlGiven: options.baseUrlGiven === true };
  }

  /** @internal The same binding, for a handle built from a sub-resource. */
  static _bound(bound: Bound): Sandboxes {
    return new Sandboxes(bound.host, { allowCustomBaseUrl: bound.allowCustomBaseUrl, baseUrlGiven: bound.baseUrlGiven });
  }

  /** Files and folders by path. */
  get files(): SandboxFiles { return new SandboxFiles(this.#bound); }
  /** File snapshots and restores. */
  get snapshots(): SandboxSnapshots { return new SandboxSnapshots(this.#bound); }
  /** The workspace's sandbox settings (read-only; changed in the Console). */
  get settings(): SandboxSettings { return new SandboxSettings(this.#bound); }
  /** Egress policy per sandbox. */
  get networkPolicy(): SandboxNetworkPolicy { return new SandboxNetworkPolicy(this.#bound); }
  /** Audited activity per sandbox. */
  get activity(): SandboxActivity { return new SandboxActivity(this.#bound); }
  /** Commands: run (a stream) and cancel. */
  get commands(): SandboxCommands { return new SandboxCommands(this.#bound); }

  /** Sandboxes, caps and provider. Returns the complete response envelope. */
  list(options: SandboxCallOptions = {}): APIPromise<T.ListWorkspaceSandboxesResponse> {
    return call(this.#bound, "sandboxes.list", {}, options);
  }
  /** Create a sandbox (every body field is optional) and return its `Sandbox` handle. Sent once, never retried. */
  async create(options: SandboxCallOptions & { body?: T.CreateWorkspaceSandboxRequest } = {}): Promise<Sandbox> {
    const { body = {}, ...rest } = options;
    const response = await call<T.CreateWorkspaceSandboxResponse>(this.#bound, "sandboxes.create", { body }, rest, true);
    return new Sandbox(this, response.sandbox);
  }
  /** Read a sandbox's record. Returns the complete response envelope (`connect` returns a handle). */
  getInfo(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.GetWorkspaceSandboxResponse> {
    return call(this.#bound, "sandboxes.getInfo", { path: { id: sandboxId } }, options);
  }
  /** A `Sandbox` handle for an existing sandbox (one `getInfo` read). */
  async connect(sandboxId: string, options: SandboxCallOptions = {}): Promise<Sandbox> {
    const response = await this.getInfo(sandboxId, options);
    return new Sandbox(this, response.sandbox);
  }
  /** Rename a sandbox or change its idle TTL (retried only on a 429 or a failure before sending). Returns the
   * complete response envelope. */
  update(sandboxId: string, options: SandboxCallOptions & { body: T.UpdateWorkspaceSandboxRequest }): APIPromise<T.UpdateWorkspaceSandboxResponse> {
    const { body, ...rest } = options;
    return call(this.#bound, "sandboxes.update", { path: { id: sandboxId }, body }, rest);
  }
  /** Destroy a sandbox and its disk. Resolves to `undefined` when a retry found it already gone (`meta.alreadyApplied`). */
  kill(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.DestroyWorkspaceSandboxResponse | undefined> {
    return call(this.#bound, "sandboxes.kill", { path: { id: sandboxId } }, options);
  }
  /** Hibernate a sandbox (its disk is kept). Sent once, never retried. Returns the complete response envelope. */
  hibernate(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.HibernateWorkspaceSandboxResponse> {
    return call(this.#bound, "sandboxes.hibernate", { path: { id: sandboxId } }, options, true);
  }
  /** Resume a hibernated sandbox. Sent once, never retried. Returns the complete response envelope. */
  resume(sandboxId: string, options: SandboxCallOptions = {}): APIPromise<T.ResumeWorkspaceSandboxResponse> {
    return call(this.#bound, "sandboxes.resume", { path: { id: sandboxId } }, options, true);
  }
}
