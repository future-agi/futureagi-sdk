/**
 * `sbx.commands`: run a command to completion, stream its frames, or cancel it. Exec is never retried, ever:
 * a second attempt would run the command again. The last frame of a complete stream is `exit` (or `error`);
 * a stream that ends without one throws `CommandIncompleteError`. Leaving a `for await` loop early (or calling
 * `return()`) closes the connection, which cancels the command.
 */

import type * as T from "../generated/platform/types.gen";
import type { ExecFrame, ExecStream, Sandboxes } from "../platform/resources/sandboxes";
import { CommandFailedError, CommandIncompleteError, mapped, SandboxConnectionError, toSandboxError } from "./errors";

/** What a command runs with. */
export interface CommandOptions {
  /** Working folder in the sandbox. */
  readonly cwd?: string;
  /** Plain, non-secret variables for this command only (never put credentials here). */
  readonly env?: Readonly<Record<string, string>>;
  /** The server stops the command after this many seconds. */
  readonly timeoutSeconds?: number;
  /** Aborting closes the stream, which cancels the command. */
  readonly signal?: AbortSignal;
}

/** `commands.run` options: the command options plus output callbacks, called as the output arrives. */
export interface RunOptions extends CommandOptions {
  readonly onStdout?: (text: string) => void;
  readonly onStderr?: (text: string) => void;
}

/**
 * A finished command: the whole `exit` record plus the output. A non-zero `exitCode`, a timeout, a signal, a
 * cancel or a spawn failure (`error`) is a result, not an error: `run()` throws only `CommandIncompleteError`
 * (no exit frame) and `CommandFailedError` (an `error` frame).
 */
export class CommandResult {
  /** The exit code; null when the process ended by a signal or never started (see `signal` and `error`). */
  readonly exitCode: number | null;
  /** The signal that ended the process (`SIGKILL`), when one did. */
  readonly signal?: string;
  /** The server stopped the command at its `timeoutSeconds`. */
  readonly timedOut: boolean;
  /** The command was cancelled (`commands.cancel`, or the stream was closed). */
  readonly cancelled: boolean;
  /** Output beyond the server's cap was dropped. */
  readonly truncated: boolean;
  /** How long the command ran, in milliseconds. */
  readonly durationMs: number;
  /** Bytes the command wrote to standard output (counted by the server, including any dropped). */
  readonly stdoutBytes: number;
  /** Bytes the command wrote to standard error (counted by the server, including any dropped). */
  readonly stderrBytes: number;
  /** Why the command could not run (a spawn failure), when it could not. */
  readonly error?: string;
  /** Everything the command wrote to standard output, in order (as received). */
  readonly stdout: string;
  /** Everything the command wrote to standard error, in order (as received). */
  readonly stderr: string;
  /** The command's id. */
  readonly execId?: string;
  /** The `exit` record as the server sent it. */
  readonly exit: T.OmegaExecExit;

  constructor(exit: T.OmegaExecExit, stdout: string, stderr: string, execId?: string) {
    this.exit = exit;
    this.exitCode = exit.exitCode ?? null;
    if (exit.signal !== undefined) this.signal = exit.signal;
    this.timedOut = exit.timedOut;
    this.cancelled = exit.cancelled;
    this.truncated = exit.truncated;
    this.durationMs = exit.durationMs;
    this.stdoutBytes = exit.stdoutBytes;
    this.stderrBytes = exit.stderrBytes;
    if (exit.error !== undefined) this.error = exit.error;
    this.stdout = stdout;
    this.stderr = stderr;
    if (execId !== undefined) this.execId = execId;
  }
}

/** A command's frames for `for await`. It throws `CommandIncompleteError` when the stream ends without an `exit`
 * (or `error`) frame, including a connection that dropped or went idle after it opened (`cause` is the
 * `SandboxConnectionError`). `return()` closes the connection, which cancels the command. */
export class CommandStream implements AsyncIterableIterator<ExecFrame> {
  readonly #inner: ExecStream;
  readonly #frames: AsyncGenerator<ExecFrame, void, undefined>;

  /** @internal Built by `sbx.commands.stream`. */
  constructor(inner: ExecStream) {
    this.#inner = inner;
    this.#frames = checked(inner);
  }

  /** The command's id, once its `started` frame was read. */
  get execId(): string | undefined {
    return this.#inner.execId;
  }

  next(): Promise<IteratorResult<ExecFrame, void>> {
    return this.#frames.next();
  }

  /** Close the connection; the server cancels a command that is still running. */
  async return(): Promise<IteratorResult<ExecFrame, void>> {
    await this.#inner.return();
    return this.#frames.return(undefined);
  }

  [Symbol.asyncIterator](): this {
    return this;
  }
}

async function* checked(inner: ExecStream): AsyncGenerator<ExecFrame, void, undefined> {
  try {
    for await (const frame of inner) {
      yield frame;
      if (frame.event === "exit" || frame.event === "error") return;
    }
  } catch (error) {
    const out = toSandboxError(error);
    // the stream opened, then the connection failed: no exit frame came, and whether the command finished is unknown
    if (out instanceof SandboxConnectionError) throw new CommandIncompleteError(inner.execId !== undefined ? { execId: inner.execId } : {}, undefined, out);
    throw out;
  }
  throw new CommandIncompleteError(inner.execId !== undefined ? { execId: inner.execId } : {});
}

function execBody(command: string, options: CommandOptions): T.ExecInWorkspaceSandboxRequest {
  return {
    command,
    ...(options.cwd !== undefined ? { cwd: options.cwd } : {}),
    ...(options.env !== undefined ? { env: { ...options.env } } : {}),
    ...(options.timeoutSeconds !== undefined ? { timeoutSeconds: options.timeoutSeconds } : {}),
  };
}

/** `sbx.commands`. */
export class Commands {
  readonly #api: Sandboxes;
  readonly #sandbox: { readonly id: string };

  /** @internal Built by `Sandbox`. */
  constructor(api: Sandboxes, sandbox: { readonly id: string }) {
    this.#api = api;
    this.#sandbox = sandbox;
  }

  /** Open the command's output stream (an HTTP refusal throws here). Never retried. */
  async stream(command: string, options: CommandOptions = {}): Promise<CommandStream> {
    const inner = await mapped(() =>
      this.#api.commands.run(this.#sandbox.id, {
        body: execBody(command, options),
        ...(options.signal !== undefined ? { signal: options.signal } : {}),
      }),
    );
    return new CommandStream(inner);
  }

  /** Run a command to its end. Resolves with the whole exit record even for a non-zero exit code, a timeout, a
   * signal, a cancel or a spawn failure; throws only `CommandIncompleteError` (the stream ended without an exit
   * frame, also when the connection dropped or went idle after the stream opened) and `CommandFailedError` (an
   * `error` frame). Before the stream opens, the request's own refusal (`UnavailableError`, ...) or transport
   * failure (`SandboxConnectionError`) is thrown as for any call. Never retried. */
  async run(command: string, options: RunOptions = {}): Promise<CommandResult> {
    const stream = await this.stream(command, options);
    let stdout = "";
    let stderr = "";
    try {
      for await (const frame of stream) {
        if (frame.event === "stdout") {
          stdout += frame.data.data;
          options.onStdout?.(frame.data.data);
        } else if (frame.event === "stderr") {
          stderr += frame.data.data;
          options.onStderr?.(frame.data.data);
        } else if (frame.event === "exit") {
          return new CommandResult(frame.data, stdout, stderr, stream.execId);
        } else if (frame.event === "error") {
          throw new CommandFailedError(frame.data.message, { ...(stream.execId !== undefined ? { execId: stream.execId } : {}), stdout, stderr });
        }
      }
    } catch (error) {
      if (error instanceof CommandIncompleteError) {
        const cause = error.cause instanceof Error ? error.cause : undefined;
        throw new CommandIncompleteError({ ...(error.execId !== undefined ? { execId: error.execId } : {}), stdout, stderr }, undefined, cause);
      }
      throw error;
    }
    throw new CommandIncompleteError({ ...(stream.execId !== undefined ? { execId: stream.execId } : {}), stdout, stderr });
  }

  /** Cancel a running command by its exec id. Never retried. Returns the complete response. */
  cancel(execId: string): Promise<T.CancelWorkspaceSandboxExecResponse> {
    return mapped(() => this.#api.commands.cancel(this.#sandbox.id, execId));
  }
}
