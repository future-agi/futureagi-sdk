// Future AGI sandboxes for the AI SDK (the `ai` package, an optional peer of @future-agi/sdk):
//
//     import { createFutureAGISandboxSession, sandboxTools } from "@future-agi/sdk/sandbox/ai-sdk";
//
// `createFutureAGISandboxSession()` is an `experimental_sandbox` for `generateText`, `streamText` and
// `ToolLoopAgent`; `sandboxTools(sandbox)` are four tools for `tools`. Both run on the `Sandbox` handle of
// "@future-agi/sdk/sandbox" and need `ai` installed (see README.md next to this file).

export {
  createFutureAGISandboxSession,
  DEFAULT_WORKING_DIRECTORY,
  type FutureAGISandboxSession,
  type FutureAGISandboxSessionOptions,
} from "./session";
export {
  DEFAULT_MAX_OUTPUT_CHARS,
  sandboxTools,
  type SandboxExecInput,
  type SandboxExecResult,
  type SandboxListFilesInput,
  type SandboxListFilesResult,
  type SandboxReadFileInput,
  type SandboxReadFileResult,
  type SandboxTools,
  type SandboxToolsOptions,
  type SandboxWriteFileInput,
  type SandboxWriteFileResult,
} from "./tools";
export {
  EXIT_CANCELLED,
  EXIT_FAILED,
  EXIT_SIGNAL_BASE,
  EXIT_TIMED_OUT,
  LINUX_SIGNALS,
  shellExitCode,
  signalNumber,
  type CommandEnding,
} from "./exit";
