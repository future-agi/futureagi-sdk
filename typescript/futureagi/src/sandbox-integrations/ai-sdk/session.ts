/**
 * A Future AGI sandbox as the AI SDK's `Experimental_SandboxSession`, for the `experimental_sandbox` option of
 * `generateText`, `streamText` and `ToolLoopAgent`:
 *
 *     import { generateText } from "ai";
 *     import { createFutureAGISandboxSession } from "@future-agi/sdk/sandbox/ai-sdk";
 *     await using sandbox = await createFutureAGISandboxSession();   // OMEGA_BASE_URL + FI_API_KEY/FI_SECRET_KEY
 *     const result = await generateText({ model, tools, prompt, experimental_sandbox: sandbox });
 *
 * Every call goes through the `Sandbox` handle of `@future-agi/sdk`. Nothing is retried: a command that may have
 * run is never sent again. `run` resolves with an exit code for every ending (./exit.ts); it throws only what the
 * handle throws (`CommandIncompleteError` when no exit frame came, `CommandFailedError` on an error frame, or the
 * request's own refusal) and a folder outside `/workspace`. Commands start in a folder inside `/workspace`: the
 * exec API takes that folder relative to `/workspace` and refuses an absolute one, so `/workspace/app` is sent as
 * `app` and `/workspace` itself as no folder at all; a folder outside `/workspace` is refused before anything is
 * sent (a command can still `cd` there). The file methods reach `/workspace` only (the files API takes paths
 * relative to it); a missing file reads as null. `spawn` is not offered: it rejects before anything is sent.
 */

import type { Experimental_SandboxSession } from "ai";

import { NotFoundError, Sandbox, SandboxError, type CreateSandboxOptions } from "../../sandbox";
import { endingNote, shellExitCode } from "./exit";

type RunOptions = Parameters<Experimental_SandboxSession["run"]>[0];
type ReadOptions = Parameters<Experimental_SandboxSession["readFile"]>[0];
type ReadTextOptions = Parameters<Experimental_SandboxSession["readTextFile"]>[0];
type WriteStreamOptions = Parameters<Experimental_SandboxSession["writeFile"]>[0];
type WriteBytesOptions = Parameters<Experimental_SandboxSession["writeBinaryFile"]>[0];
type WriteTextOptions = Parameters<Experimental_SandboxSession["writeTextFile"]>[0];

/** The sandbox's writable folder, where commands run and relative file paths resolve unless told otherwise. */
export const DEFAULT_WORKING_DIRECTORY = "/workspace";

/** How `createFutureAGISandboxSession` gets its sandbox and runs commands in it. */
export interface FutureAGISandboxSessionOptions {
  /** An existing sandbox (from `Sandbox.connect`, `Sandbox.create` or `client.sandboxes`); else one is created. */
  readonly sandbox?: Sandbox;
  /** The create options used when `sandbox` is absent (`Sandbox.create`, which reads the environment). */
  readonly create?: CreateSandboxOptions;
  /** Where commands run and relative file paths resolve (default `/workspace`): a folder inside `/workspace`,
   * absolute or relative to it. A folder outside `/workspace` is refused before a sandbox is created. */
  readonly workingDirectory?: string;
  /** The server stops each command after this many seconds (at least 1); absent, the workspace default applies. */
  readonly timeoutSeconds?: number;
  /** The workspace's limit, `caps.exec.maxTimeoutSeconds` from `Sandbox.list()`; `timeoutSeconds` is capped to it. */
  readonly maxTimeoutSeconds?: number;
  /** The text the AI SDK may add to the agent's instructions (default: one that names the working folder). */
  readonly description?: string;
  /** Delete the sandbox on `dispose()` (default: only a sandbox this function created). */
  readonly deleteOnDispose?: boolean;
}

/** A sandbox session: the AI SDK's `Experimental_SandboxSession`, plus the handle and `dispose`. */
export interface FutureAGISandboxSession extends Experimental_SandboxSession {
  /** The sandbox handle, for anything the session does not cover. */
  readonly sandbox: Sandbox;
  /** Where commands run and relative file paths resolve: an absolute folder inside `/workspace`. */
  readonly workingDirectory: string;
  /** Delete the sandbox when the session owns it (see `deleteOnDispose`); a second call does nothing. */
  dispose(): Promise<void>;
  /** `await using` calls `dispose()`. */
  [Symbol.asyncDispose](): Promise<void>;
}

/** An integer number of seconds of at least 1, capped to `max` when given; undefined leaves the default. */
export function clampTimeout(seconds: number | undefined, max?: number): number | undefined {
  const cap = max !== undefined && Number.isFinite(max) && max >= 1 ? Math.floor(max) : undefined;
  if (seconds === undefined || Number.isNaN(seconds)) return undefined;
  if (!Number.isFinite(seconds)) return seconds > 0 ? cap : 1;
  const whole = Math.max(1, Math.ceil(seconds));
  return cap !== undefined ? Math.min(whole, cap) : whole;
}

/** `path` resolved against `base` (POSIX rules: `.` and `..` segments folded); an absolute path keeps its root. */
export function resolvePath(base: string, path: string): string {
  const joined = path.startsWith("/") ? path : `${base}/${path}`;
  const parts: string[] = [];
  for (const part of joined.split("/")) {
    if (part === "" || part === ".") continue;
    if (part === "..") parts.pop();
    else parts.push(part);
  }
  if (joined.startsWith("/")) return `/${parts.join("/")}`;
  return parts.length > 0 ? parts.join("/") : ".";
}

/**
 * The files-API path for `path` resolved against `base`. The files API takes paths relative to the sandbox's
 * `/workspace` folder, so `/workspace/src/a.ts` is sent as `src/a.ts`; a path outside `/workspace` is refused
 * before anything is sent (read or copy it with a command instead).
 */
export function filesPath(base: string, path: string): string {
  const resolved = resolvePath(base, path);
  if (!resolved.startsWith("/")) return resolved;
  if (resolved === DEFAULT_WORKING_DIRECTORY) return ".";
  if (resolved.startsWith(`${DEFAULT_WORKING_DIRECTORY}/`)) return resolved.slice(DEFAULT_WORKING_DIRECTORY.length + 1);
  throw new SandboxError(
    `${resolved} is outside ${DEFAULT_WORKING_DIRECTORY}: the sandbox's file calls reach only that folder (use a command such as cat or cp)`,
    { code: "outside_workspace", operation: "sandbox.files" },
  );
}

/** `folder` (absolute) relative to `/workspace`: "" for `/workspace` itself, undefined for a folder outside it. */
function underWorkspace(folder: string): string | undefined {
  if (folder === DEFAULT_WORKING_DIRECTORY) return "";
  return folder.startsWith(`${DEFAULT_WORKING_DIRECTORY}/`) ? folder.slice(DEFAULT_WORKING_DIRECTORY.length + 1) : undefined;
}

function outsideFolder(folder: string): SandboxError {
  return new SandboxError(
    `${folder} is outside ${DEFAULT_WORKING_DIRECTORY}: commands start in a folder inside it (to work in ${folder}, ` +
      "begin the command with cd)",
    { code: "outside_workspace", operation: "sandbox.commands" },
  );
}

/**
 * A working folder as an absolute folder inside `/workspace` (a relative one is under `/workspace`). A folder
 * outside `/workspace` is refused: commands cannot start there.
 */
export function workingFolder(path: string = DEFAULT_WORKING_DIRECTORY): string {
  const folder = resolvePath(DEFAULT_WORKING_DIRECTORY, path);
  if (underWorkspace(folder) === undefined) throw outsideFolder(folder);
  return folder;
}

/**
 * The exec API's `cwd` for the folder `path` resolved against `base` (a relative `base` is under `/workspace`).
 * The exec API takes the folder relative to `/workspace` and refuses an absolute one, so `/workspace/app` is sent
 * as `app` and `/workspace` itself as no `cwd` at all (undefined). A folder outside `/workspace` is refused before
 * anything is sent.
 */
export function execCwd(base: string, path: string): string | undefined {
  const folder = resolvePath(resolvePath(DEFAULT_WORKING_DIRECTORY, base), path);
  const inside = underWorkspace(folder);
  if (inside === undefined) throw outsideFolder(folder);
  return inside === "" ? undefined : inside;
}

/** `text` followed by `line` on a line of its own. */
function withLine(text: string, line: string): string {
  if (text === "") return line;
  return text.endsWith("\n") ? `${text}${line}` : `${text}\n${line}`;
}

/** Lines `start` to `end` (1-based, inclusive, line endings kept); past the end reads to the end. */
function lineRange(text: string, start = 1, end?: number): string {
  if (start <= 1 && end === undefined) return text;
  const lines: string[] = [];
  let from = 0;
  while (from < text.length) {
    const newline = text.indexOf("\n", from);
    const to = newline === -1 ? text.length : newline + 1;
    lines.push(text.slice(from, to));
    from = to;
  }
  return lines.slice(Math.max(1, start) - 1, end).join("");
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<Uint8Array> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    size += value.byteLength;
  }
  const out = new Uint8Array(size);
  let at = 0;
  for (const chunk of chunks) {
    out.set(chunk, at);
    at += chunk.byteLength;
  }
  return out;
}

const isUtf8 = (encoding: string | undefined): boolean =>
  encoding === undefined || ["utf-8", "utf8"].includes(encoding.toLowerCase());

class Session implements FutureAGISandboxSession {
  readonly sandbox: Sandbox;
  readonly workingDirectory: string;
  readonly description: string;
  readonly #timeoutSeconds: number | undefined;
  readonly #deleteOnDispose: boolean;
  #disposed = false;

  constructor(sandbox: Sandbox, options: FutureAGISandboxSessionOptions, workingDirectory: string, deleteOnDispose: boolean) {
    this.sandbox = sandbox;
    this.workingDirectory = workingDirectory;
    this.#timeoutSeconds = clampTimeout(options.timeoutSeconds, options.maxTimeoutSeconds);
    this.#deleteOnDispose = deleteOnDispose;
    this.description =
      options.description ??
      `A Future AGI sandbox (${sandbox.id}): an isolated Linux computer. Commands run with /bin/sh -c in ` +
        `${this.workingDirectory}; files written there stay until the sandbox is deleted. Exit code 124 means the ` +
        `command timed out, 128+N that signal N ended it, 130 that it was cancelled.`;
  }

  readonly run = async (options: RunOptions): Promise<{ exitCode: number; stdout: string; stderr: string }> => {
    options.abortSignal?.throwIfAborted();
    const timeoutSeconds = this.#timeoutSeconds;
    const cwd = execCwd(this.workingDirectory, options.workingDirectory ?? ".");
    const result = await this.sandbox.commands.run(options.command, {
      ...(cwd !== undefined ? { cwd } : {}),
      ...(options.env !== undefined ? { env: options.env } : {}),
      ...(timeoutSeconds !== undefined ? { timeoutSeconds } : {}),
      ...(options.abortSignal !== undefined ? { signal: options.abortSignal } : {}),
    });
    const note = endingNote(result, timeoutSeconds);
    return { exitCode: shellExitCode(result), stdout: result.stdout, stderr: note !== undefined ? withLine(result.stderr, note) : result.stderr };
  };

  readonly spawn: FutureAGISandboxSession["spawn"] = async (): Promise<never> => {
    throw new SandboxError(
      "spawn is not offered by the Future AGI sandbox session: use run, which waits for the command to end",
      { code: "not_offered", operation: "sandbox.spawn" },
    );
  };

  readonly readBinaryFile = async (options: ReadOptions): Promise<Uint8Array | null> => {
    options.abortSignal?.throwIfAborted();
    const path = filesPath(this.workingDirectory, options.path);
    let data: Uint8Array;
    try {
      data = await this.sandbox.files.download(path);
    } catch (error) {
      if (error instanceof NotFoundError) return null;
      throw error;
    }
    options.abortSignal?.throwIfAborted();
    return data;
  };

  readonly readFile = async (options: ReadOptions): Promise<ReadableStream<Uint8Array> | null> => {
    const data = await this.readBinaryFile(options);
    if (data === null) return null;
    return new ReadableStream<Uint8Array>({
      start(controller) {
        if (data.byteLength > 0) controller.enqueue(data);
        controller.close();
      },
    });
  };

  readonly readTextFile = async (options: ReadTextOptions): Promise<string | null> => {
    const data = await this.readBinaryFile(options);
    if (data === null) return null;
    return lineRange(new TextDecoder(options.encoding ?? "utf-8").decode(data), options.startLine, options.endLine);
  };

  readonly writeBinaryFile = async (options: WriteBytesOptions): Promise<void> => {
    options.abortSignal?.throwIfAborted();
    // files.write creates missing parent folders and replaces an existing file
    await this.sandbox.files.write(filesPath(this.workingDirectory, options.path), options.content);
  };

  readonly writeFile = async (options: WriteStreamOptions): Promise<void> => {
    options.abortSignal?.throwIfAborted();
    const content = await collect(options.content);
    await this.writeBinaryFile({ path: options.path, content, ...(options.abortSignal !== undefined ? { abortSignal: options.abortSignal } : {}) });
  };

  readonly writeTextFile = async (options: WriteTextOptions): Promise<void> => {
    options.abortSignal?.throwIfAborted();
    if (!isUtf8(options.encoding)) throw new TypeError(`writeTextFile writes UTF-8 only, not ${String(options.encoding)}`);
    await this.sandbox.files.write(filesPath(this.workingDirectory, options.path), options.content);
  };

  async dispose(): Promise<void> {
    if (this.#disposed) return;
    if (this.#deleteOnDispose) await this.sandbox.delete();
    this.#disposed = true;
  }

  async [Symbol.asyncDispose](): Promise<void> {
    await this.dispose();
  }
}

/**
 * A sandbox session for the AI SDK. With `sandbox`, it wraps that handle; otherwise it creates a sandbox with
 * `Sandbox.create(create)` (the environment's credentials). `dispose()` deletes the sandbox only when this
 * function created it, unless `deleteOnDispose` says otherwise. A `workingDirectory` outside `/workspace` is
 * refused before anything is sent. Never retried.
 */
export async function createFutureAGISandboxSession(options: FutureAGISandboxSessionOptions = {}): Promise<FutureAGISandboxSession> {
  if (options.sandbox !== undefined && options.create !== undefined) {
    throw new TypeError("createFutureAGISandboxSession takes sandbox or create, not both");
  }
  const workingDirectory = workingFolder(options.workingDirectory);
  const created = options.sandbox === undefined;
  const sandbox = options.sandbox ?? (await Sandbox.create(options.create ?? {}));
  return new Session(sandbox, options, workingDirectory, options.deleteOnDispose ?? created);
}
