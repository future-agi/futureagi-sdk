/**
 * AI SDK tools bound to one Future AGI sandbox: spread them into `tools` of `generateText`, `streamText` or a
 * `ToolLoopAgent`.
 *
 *     const sbx = await Sandbox.create();
 *     const result = await generateText({ model, prompt, tools: { ...sandboxTools(sbx) } });
 *
 * The names, inputs and results are those of the Python MCP server's tools for one sandbox
 * (`futureagi sandbox mcp --sandbox ID`): `sandbox_exec`, `sandbox_read_file`, `sandbox_write_file` and
 * `sandbox_list_files`. A non-zero exit, a timeout, a signal and a cancel are results the model reads; a refusal
 * or a stream with no exit frame is thrown, and the AI SDK hands the error to the model. No tool takes an `env`
 * (exec variables must never carry credentials), and nothing is retried. The file tools reach `/workspace` only,
 * like the files API. `sandbox_exec` starts a command in a folder inside `/workspace` (the exec API takes that
 * folder relative to `/workspace`); a `cwd` outside it is refused before anything is sent, and a command can still
 * `cd` elsewhere.
 */

import { jsonSchema, tool, type Tool } from "ai";

import type { Sandbox } from "../../sandbox";
import { clampTimeout, execCwd, filesPath, resolvePath, workingFolder } from "./session";

/** Output characters each of stdout and stderr keeps (the newest ones), as in the Python MCP server. */
export const DEFAULT_MAX_OUTPUT_CHARS = 20_000;

/** How the tools run commands and resolve paths. */
export interface SandboxToolsOptions {
  /** Where commands run and relative paths resolve (default `/workspace`): a folder inside `/workspace`, absolute
   * or relative to it. A folder outside `/workspace` is refused when the tools are built. */
  readonly workingDirectory?: string;
  /** The default limit in seconds for `sandbox_exec` when the model gives none; absent, the workspace default. */
  readonly timeoutSeconds?: number;
  /** The workspace's limit, `caps.exec.maxTimeoutSeconds` from `Sandbox.list()`; every timeout is capped to it. */
  readonly maxTimeoutSeconds?: number;
  /** Characters each of stdout and stderr keeps (default 20000). */
  readonly maxOutputChars?: number;
}

/** `sandbox_exec` input. */
export interface SandboxExecInput {
  readonly command: string;
  readonly cwd?: string;
  readonly timeout_seconds?: number;
}

/** `sandbox_exec` result: the whole exit record, with stdout and stderr clipped to their newest characters. */
export interface SandboxExecResult {
  readonly exit_code: number | null;
  readonly signal: string | null;
  readonly timed_out: boolean;
  readonly cancelled: boolean;
  readonly truncated: boolean;
  readonly duration_ms: number;
  readonly error: string | null;
  readonly exec_id: string | null;
  readonly stdout: string;
  readonly stderr: string;
  readonly stdout_clipped: boolean;
  readonly stderr_clipped: boolean;
}

/** `sandbox_read_file` input. */
export interface SandboxReadFileInput {
  readonly path: string;
  readonly max_bytes?: number;
}

/** `sandbox_read_file` result: text as UTF-8, anything else as base64, with the server's `bytes`; `truncated`
 * when the content stops before the end of the file (at `max_bytes` or the workspace's read limit). */
export interface SandboxReadFileResult {
  readonly path: string;
  readonly encoding: "utf8" | "base64";
  readonly content: string;
  readonly bytes: number;
  readonly truncated: boolean;
}

/** `sandbox_write_file` input. */
export interface SandboxWriteFileInput {
  readonly path: string;
  readonly content: string;
  readonly encoding?: "utf8" | "base64";
}

/** `sandbox_write_file` result. */
export interface SandboxWriteFileResult {
  readonly path: string;
  readonly bytes: number;
}

/** `sandbox_list_files` input. */
export interface SandboxListFilesInput {
  readonly path?: string;
}

/** `sandbox_list_files` result. */
export interface SandboxListFilesResult {
  readonly path: string;
  readonly entries: { readonly name: string; readonly size: number; readonly directory: boolean; readonly mode: string }[];
}

/** The four sandbox tools, keyed by the names the model sees. */
export type SandboxTools = {
  sandbox_exec: Tool<SandboxExecInput, SandboxExecResult>;
  sandbox_read_file: Tool<SandboxReadFileInput, SandboxReadFileResult>;
  sandbox_write_file: Tool<SandboxWriteFileInput, SandboxWriteFileResult>;
  sandbox_list_files: Tool<SandboxListFilesInput, SandboxListFilesResult>;
};

/** The newest `max` characters of `text`, after a first line that counts the dropped ones. */
export function clipOutput(text: string, max: number): { text: string; clipped: boolean } {
  if (text.length <= max) return { text, clipped: false };
  let start = text.length - max;
  // never start inside a surrogate pair
  const first = text.charCodeAt(start);
  if (first >= 0xdc00 && first <= 0xdfff) start += 1;
  return { text: `[... ${start} earlier characters dropped ...]\n${text.slice(start)}`, clipped: true };
}

function fromBase64(text: string): Uint8Array {
  const binary = atob(text);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
  return out;
}

/** AI SDK tools that run commands and edit files in `sandbox`. */
export function sandboxTools(sandbox: Sandbox, options: SandboxToolsOptions = {}): SandboxTools {
  const workingDirectory = workingFolder(options.workingDirectory);
  const maxOutputChars = Math.max(1, Math.floor(options.maxOutputChars ?? DEFAULT_MAX_OUTPUT_CHARS));
  const at = (path: string): string => resolvePath(workingDirectory, path);

  const sandbox_exec = tool({
    description:
      `Run a shell command (/bin/sh -c) in the sandbox and wait for it to end. It runs in ${workingDirectory} unless ` +
      "cwd says otherwise. The result is the whole exit record: exit_code is null when a signal ended the command " +
      "or it never started; a timeout, a signal and a cancel are reported, not raised.",
    inputSchema: jsonSchema<SandboxExecInput>({
      type: "object",
      properties: {
        command: { type: "string", description: "The shell command to run." },
        cwd: {
          type: "string",
          description:
            `The folder to run it in (default ${workingDirectory}): a folder inside /workspace, relative to ` +
            `${workingDirectory} or absolute. To work outside /workspace, begin the command with cd.`,
        },
        timeout_seconds: { type: "integer", minimum: 1, description: "Stop the command after this many seconds (the workspace limit applies)." },
      },
      required: ["command"],
      additionalProperties: false,
    }),
    execute: async (input: SandboxExecInput, { abortSignal }): Promise<SandboxExecResult> => {
      const timeoutSeconds = clampTimeout(input.timeout_seconds ?? options.timeoutSeconds, options.maxTimeoutSeconds);
      const cwd = execCwd(workingDirectory, input.cwd ?? ".");
      const result = await sandbox.commands.run(input.command, {
        ...(cwd !== undefined ? { cwd } : {}),
        ...(timeoutSeconds !== undefined ? { timeoutSeconds } : {}),
        ...(abortSignal !== undefined ? { signal: abortSignal } : {}),
      });
      const stdout = clipOutput(result.stdout, maxOutputChars);
      const stderr = clipOutput(result.stderr, maxOutputChars);
      return {
        exit_code: result.exitCode,
        signal: result.signal ?? null,
        timed_out: result.timedOut,
        cancelled: result.cancelled,
        truncated: result.truncated,
        duration_ms: result.durationMs,
        error: result.error ?? null,
        exec_id: result.execId ?? null,
        stdout: stdout.text,
        stderr: stderr.text,
        stdout_clipped: stdout.clipped,
        stderr_clipped: stderr.clipped,
      };
    },
  });

  const sandbox_read_file = tool({
    description:
      "Read a file from the sandbox (text as UTF-8, other files as base64; encoding says which). max_bytes reads at " +
      "most that many bytes; truncated says the file is longer than the content returned.",
    inputSchema: jsonSchema<SandboxReadFileInput>({
      type: "object",
      properties: {
        path: { type: "string", description: `The file's path inside /workspace (relative paths are under ${workingDirectory}).` },
        max_bytes: { type: "integer", minimum: 1, description: "Read at most this many bytes." },
      },
      required: ["path"],
      additionalProperties: false,
    }),
    execute: async (input: SandboxReadFileInput): Promise<SandboxReadFileResult> => {
      const path = at(input.path);
      const maxBytes = input.max_bytes !== undefined ? Math.max(1, Math.floor(input.max_bytes)) : undefined;
      const file = await sandbox.files.readRecord(filesPath(workingDirectory, path), maxBytes !== undefined ? { maxBytes } : {});
      return { path, encoding: file.encoding, content: file.content, bytes: file.bytes, truncated: file.truncated };
    },
  });

  const sandbox_write_file = tool({
    description: "Write a file in the sandbox; missing folders are created and an existing file is replaced.",
    inputSchema: jsonSchema<SandboxWriteFileInput>({
      type: "object",
      properties: {
        path: { type: "string", description: `The file's path inside /workspace (relative paths are under ${workingDirectory}).` },
        content: { type: "string", description: "The file's content: text, or base64 when encoding is base64." },
        encoding: { type: "string", enum: ["utf8", "base64"], description: "utf8 (default) or base64." },
      },
      required: ["path", "content"],
      additionalProperties: false,
    }),
    execute: async (input: SandboxWriteFileInput): Promise<SandboxWriteFileResult> => {
      const path = at(input.path);
      const target = filesPath(workingDirectory, path);
      const data = input.encoding === "base64" ? fromBase64(input.content) : input.content;
      const response = await sandbox.files.write(target, data);
      return { path, bytes: response.file.bytes };
    },
  });

  const sandbox_list_files = tool({
    description: "List a folder in the sandbox.",
    inputSchema: jsonSchema<SandboxListFilesInput>({
      type: "object",
      properties: {
        path: { type: "string", description: `The folder, inside /workspace (default ${workingDirectory}).` },
      },
      additionalProperties: false,
    }),
    execute: async (input: SandboxListFilesInput): Promise<SandboxListFilesResult> => {
      const path = at(input.path ?? ".");
      const entries = await sandbox.files.list(filesPath(workingDirectory, path));
      return {
        path,
        entries: entries.map((entry) => ({ name: entry.name, size: entry.size, directory: entry.directory === true, mode: entry.mode })),
      };
    },
  });

  return { sandbox_exec, sandbox_read_file, sandbox_write_file, sandbox_list_files };
}
