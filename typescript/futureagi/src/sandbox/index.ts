// Hosted sandboxes: the `Sandbox` handle, its errors, and the `client.sandboxes` layer under it.
//
//     import { FutureAGIClient, Sandbox, SandboxError } from "@future-agi/sdk";
//     await using sbx = await Sandbox.create();   // OMEGA_BASE_URL; FI_API_KEY + FI_SECRET_KEY or FUTUREAGI_OMEGA_API_KEY
//     console.log((await sbx.commands.run("uname -a")).stdout);
//
// The package root exports the sandbox-only names (Sandbox, SandboxError, the Command* classes, ...). The status
// errors here share their names with the root error classes and extend them; import them from
// "@future-agi/sdk/sandbox" (or alias them) next to the root ones.

export { Sandbox, type CreateSandboxOptions, type SandboxInfo, type SandboxList, type SandboxSettingsInfo } from "./sandbox";
export { SANDBOX_ENV } from "./config";
export { CommandResult, CommandStream, Commands, type CommandOptions, type RunOptions } from "./commands";
export {
  Files,
  NetworkPolicy,
  Snapshots,
  type FileEntry,
  type NetworkPolicyRecord,
  type NetworkPolicyState,
  type SnapshotInfo,
} from "./parts";
export {
  AuthenticationError,
  CommandFailedError,
  CommandIncompleteError,
  ConflictError,
  InsufficientStorageError,
  NotFoundError,
  PermissionDeniedError,
  PreconditionRequiredError,
  ProviderError,
  QuotaExceededError,
  RateLimitError,
  SandboxConnectionError,
  SandboxError,
  SandboxHibernatedError,
  SandboxStateError,
  UnavailableError,
  UnprocessableEntityError,
  ValidationError,
  type CommandOutput,
  type SandboxErrorFields,
} from "./errors";
export {
  ExecStream,
  SandboxActivity,
  SandboxCommands,
  SandboxFiles,
  SandboxNetworkPolicy,
  Sandboxes,
  SandboxSettings,
  SandboxSnapshots,
  type ExecFrame,
  type SandboxCallOptions,
  type UnknownExecFrame,
  type UploadBody,
} from "../platform/resources/sandboxes";
