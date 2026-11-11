/**
 * The `Sandbox` handle: an isolated computer that runs commands and keeps files.
 *
 *     import { FutureAGIClient, Sandbox, SandboxError } from "@future-agi/sdk";
 *     await using sbx = await Sandbox.create({ name: "demo" });   // OMEGA_BASE_URL + FI_API_KEY/FI_SECRET_KEY
 *     const result = await sbx.commands.run("echo hello");        // result.exitCode, result.stdout
 *
 * `Sandbox.create`, `Sandbox.connect`, `Sandbox.list` and `Sandbox.settings` read the environment only
 * (./config.ts). To pass keys, a base URL, a workspace or an organization in code, build a client:
 *
 *     const client = new FutureAGIClient({ platformBaseUrl: "https://ee.internal:8443", platformToken, allowCustomBaseUrl: true });
 *     const sbx = await client.sandboxes.create({ body: { name: "demo" } });   // the same Sandbox handle
 *
 * Every method calls `client.sandboxes` (src/platform/resources/sandboxes.ts) and throws the sandbox errors
 * of `./errors`. No method retries a call that changes something, and none resumes a hibernated sandbox.
 * `await using` deletes the sandbox when the block ends; if the block threw and the delete failed too, the
 * runtime throws a `SuppressedError` whose `suppressed` is the block's own error and whose `error` is the
 * delete failure, so neither is lost.
 *
 * The handle holds its client in a private field: `toString()`, `toJSON()`, `util.inspect` and its errors
 * never show a credential.
 */

import type * as T from "../generated/platform/types.gen";
import { Handle } from "../_core/handles";
import { Sandboxes } from "../platform/resources/sandboxes";
import { Commands } from "./commands";
import { environmentHost } from "./config";
import { mapped, NotFoundError, toSandboxError } from "./errors";
import { Files, NetworkPolicy, Snapshots } from "./parts";

/** A sandbox record, as the server last described it. */
export type SandboxInfo = T.GetWorkspaceSandboxResponse["sandbox"];

/** `Sandbox.list()`: the workspace's sandboxes and what it may create. */
export interface SandboxList {
  readonly sandboxes: SandboxInfo[];
  readonly caps: T.ListWorkspaceSandboxesResponse["caps"];
  readonly provider: T.ListWorkspaceSandboxesResponse["provider"];
}

/** `Sandbox.create()`: the create body; every field is optional (a name-only create uses the deployment's defaults). */
export type CreateSandboxOptions = T.CreateWorkspaceSandboxRequest;

/** The workspace's sandbox settings, caps, templates and sizes. */
export type SandboxSettingsInfo = T.GetWorkspaceSandboxSettingsResponse;

const CREATE_FIELDS = [
  "name", "template", "size", "image", "environmentId", "limits", "network", "networkPolicy", "idleTtlSeconds",
] as const;

function createBody(options: CreateSandboxOptions): T.CreateWorkspaceSandboxRequest {
  const body: Record<string, unknown> = {};
  for (const field of CREATE_FIELDS) if (options[field] !== undefined) body[field] = options[field];
  return body as T.CreateWorkspaceSandboxRequest;
}

/** `client.sandboxes` over a client built from the environment; a configuration error is a thrown error. */
const fromEnvironment = (): Sandboxes => new Sandboxes(environmentHost());

const INSPECT = Symbol.for("nodejs.util.inspect.custom");

/** One hosted sandbox. Build it with `Sandbox.create`, `Sandbox.connect` or `client.sandboxes`. */
export class Sandbox extends Handle<SandboxInfo> {
  protected readonly noun = "sandbox";
  /** Run, stream and cancel commands. */
  readonly commands: Commands;
  /** Files and folders. */
  readonly files: Files;
  /** File snapshots; `restore` returns a new sandbox. */
  readonly snapshots: Snapshots;
  /** The egress policy. */
  readonly networkPolicy: NetworkPolicy;
  readonly #api: Sandboxes;
  #info: SandboxInfo;

  /** @internal Built by `client.sandboxes` and the static constructors. */
  constructor(api: Sandboxes, info: SandboxInfo) {
    super(info);
    this.#api = api;
    this.#info = info;
    this.commands = new Commands(api, this);
    this.files = new Files(api, this);
    this.snapshots = new Snapshots(api, this);
    this.networkPolicy = new NetworkPolicy(api, this);
  }

  /** Create a sandbox (state active) from the environment's client. A name-only create uses the deployment's
   * defaults. Never retried. With keys or a base URL in code, use `client.sandboxes.create`. */
  static async create(options: CreateSandboxOptions = {}): Promise<Sandbox> {
    const body = createBody(options);
    return mapped(() => fromEnvironment().create({ body }));
  }

  /** A handle for an existing sandbox, from the environment's client (or `client.sandboxes.connect`). */
  static async connect(sandboxId: string): Promise<Sandbox> {
    return mapped(() => fromEnvironment().connect(sandboxId));
  }

  /** The workspace's sandboxes, its caps and the provider, from the environment's client. */
  static async list(): Promise<SandboxList> {
    const response = await mapped(() => fromEnvironment().list());
    return { sandboxes: response.sandboxes, caps: response.caps, provider: response.provider };
  }

  /**
   * The workspace's sandbox settings, caps, templates and sizes, from the environment's client. Read-only:
   * sandbox settings are changed in the Console, from an owner's or admin's signed-in session; the SDK never
   * changes them.
   */
  static async settings(): Promise<SandboxSettingsInfo> {
    return mapped(() => fromEnvironment().settings.get());
  }

  /** The sandbox id. */
  get id(): string {
    return this.#info.id;
  }

  /** The last record read (`refresh()` re-reads it). */
  get info(): SandboxInfo {
    return this.#info;
  }

  /** The same record as `info`. */
  get data(): SandboxInfo {
    return this.#info;
  }

  /** `active`, `hibernated`, `recovery_required` or `destroyed`, as last read. */
  get state(): SandboxInfo["state"] {
    return this.#info.state;
  }

  /** The same as `state`. */
  get status(): unknown {
    return this.#info.state;
  }

  /** A deep copy of `info`. */
  toJSON(): SandboxInfo {
    return JSON.parse(JSON.stringify(this.#info)) as SandboxInfo;
  }

  toString(): string {
    return `Sandbox(${this.#info.id}, ${this.#info.state})`;
  }

  protected async fetchData(): Promise<SandboxInfo> {
    const response = await mapped(() => this.#api.getInfo(this.id));
    this.#info = response.sandbox;
    return this.#info;
  }

  protected isDone(): boolean {
    return this.#info.state === "destroyed";
  }

  /** Rename the sandbox or change its idle TTL; returns the updated record. Never retried. */
  async update(fields: T.UpdateWorkspaceSandboxRequest): Promise<SandboxInfo> {
    const response = await mapped(() => this.#api.update(this.id, { body: { ...fields } }));
    this.#info = response.sandbox;
    return this.#info;
  }

  /** Hibernate (the disk is kept); returns the updated record. Never retried. */
  async hibernate(): Promise<SandboxInfo> {
    const response = await mapped(() => this.#api.hibernate(this.id));
    this.#info = response.sandbox;
    return this.#info;
  }

  /** Resume a hibernated sandbox; returns the updated record. Never retried. */
  async resume(): Promise<SandboxInfo> {
    const response = await mapped(() => this.#api.resume(this.id));
    this.#info = response.sandbox;
    return this.#info;
  }

  /** Destroy the sandbox and its disk; returns the final record (state destroyed). A sandbox that is already
   * gone (404) is not an error here. */
  async delete(): Promise<SandboxInfo> {
    let response: T.DestroyWorkspaceSandboxResponse | undefined;
    try {
      response = await this.#api.kill(this.id);
    } catch (error) {
      const mappedError = toSandboxError(error);
      if (!(mappedError instanceof NotFoundError)) throw mappedError;
    }
    this.#info = response?.sandbox ?? { ...this.#info, state: "destroyed" };
    return this.#info;
  }

  /** The sandbox's audited activity, newest first. */
  async activity(): Promise<T.ListWorkspaceSandboxActivityResponse["activity"]> {
    const response = await mapped(() => this.#api.activity.list(this.id));
    return response.activity;
  }

  /** `await using` deletes the sandbox. */
  async dispose(): Promise<void> {
    await this.delete();
  }

  async [Symbol.asyncDispose](): Promise<void> {
    await this.delete();
  }
}

// `util.inspect(sbx)` prints `toString()`. Set on the prototype rather than declared in the class: `Handle`
// keys its dispose method by a `symbol`, so every symbol-keyed member of a subclass must be a dispose method.
Object.defineProperty(Sandbox.prototype, INSPECT, {
  value(this: Sandbox): string {
    return this.toString();
  },
  writable: true,
  configurable: true,
  enumerable: false,
});
