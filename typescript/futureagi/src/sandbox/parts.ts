/**
 * `sbx.files`, `sbx.snapshots` and `sbx.networkPolicy`. Each method calls `client.sandboxes` once (the
 * network policy's `set` reads the current revision first when no `ifMatch` is given) and throws sandbox errors.
 * Nothing that changes a file is retried.
 */

import { v4 as uuidv4 } from "uuid";

import type * as T from "../generated/platform/types.gen";
import type { Sandboxes, UploadBody } from "../platform/resources/sandboxes";
import { mapped } from "./errors";
import type { Sandbox } from "./sandbox";

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

/** `sbx.files`: paths are inside the sandbox; a relative path is under its working folder. */
export class Files {
  readonly #api: Sandboxes;
  readonly #sandbox: Bound;

  /** @internal Built by `Sandbox`. */
  constructor(api: Sandboxes, sandbox: Bound) {
    this.#api = api;
    this.#sandbox = sandbox;
  }

  /** The entries of a folder (default: the working folder). */
  async list(path = "."): Promise<FileEntry[]> {
    const response = await mapped(() => this.#api.files.list(this.#sandbox.id, { path }));
    return response.entries;
  }

  /** A file's content, bounded by `maxBytes`: a string for text, bytes for anything else. Check `truncated`
   * on `client.sandboxes.files.read` when the size matters. */
  async read(path: string, options: { maxBytes?: number } = {}): Promise<string | Uint8Array> {
    const response = await mapped(() => this.#api.files.read(this.#sandbox.id, path, options));
    return response.file.encoding === "base64" ? fromBase64(response.file.content) : response.file.content;
  }

  /** Write a small text or binary file (audited; up to the JSON body limit). Never retried. */
  write(path: string, data: string | Uint8Array | ArrayBuffer): Promise<T.WriteWorkspaceSandboxFileResponse> {
    const body: T.WriteWorkspaceSandboxFileRequest =
      typeof data === "string"
        ? { content: data, encoding: "utf8" }
        : { content: toBase64(data instanceof ArrayBuffer ? new Uint8Array(data) : data), encoding: "base64" };
    return mapped(() => this.#api.files.write(this.#sandbox.id, path, { body }));
  }

  /** Upload raw bytes, a Blob (`await fs.openAsBlob(file)`) or text; the folder must exist. Never retried. */
  upload(path: string, data: UploadBody): Promise<T.UploadWorkspaceSandboxFileResponse> {
    return mapped(() => this.#api.files.upload(this.#sandbox.id, path, { body: data }));
  }

  /** A file's raw bytes. */
  download(path: string): Promise<Uint8Array> {
    return mapped(() => this.#api.files.download(this.#sandbox.id, path));
  }

  /** Download to `localPath`: written to a temporary file next to it, renamed only once complete (Node.js). */
  async downloadTo(path: string, localPath: string): Promise<string> {
    const data = await this.download(path);
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

  /** Delete a file, or a folder with `recursive`. Never retried. */
  remove(path: string, options: { recursive?: boolean } = {}): Promise<T.DeleteWorkspaceSandboxPathResponse> {
    return mapped(() => this.#api.files.remove(this.#sandbox.id, path, options));
  }

  /** Move or rename a file or folder. Never retried. */
  move(source: string, destination: string): Promise<T.MoveWorkspaceSandboxPathResponse> {
    return mapped(() => this.#api.files.rename(this.#sandbox.id, { body: { from: source, to: destination } }));
  }

  /** Create a folder. Never retried. */
  makeDir(path: string): Promise<T.CreateWorkspaceSandboxFolderResponse> {
    return mapped(() => this.#api.files.makeDir(this.#sandbox.id, path));
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
