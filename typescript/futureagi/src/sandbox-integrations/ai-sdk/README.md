# Future AGI sandboxes for the AI SDK

`@future-agi/sdk/sandbox/ai-sdk` runs the commands and file edits of an AI SDK agent in a Future AGI sandbox: an
isolated Linux computer whose `/workspace` folder keeps its files until the sandbox is deleted.

These integrations ship in the Future AGI SDK (`npm i @future-agi/sdk`).

## Install

```bash
npm i @future-agi/sdk ai
```

`ai` is an optional peer of `@future-agi/sdk`: only this subpath needs it. It is tested with `ai` 7.0.156 and accepts
`>=7.0.156 <7.1.0`, because the AI SDK's sandbox interface is experimental and "can change in patch releases".
`ai` 7 needs Node.js 22 or later, so this subpath does too. `import` works on any Node.js 22. `require()` of this
subpath needs Node.js 22.12 or later: `ai` ships only ES modules, and Node.js loads an ES module through `require()`
from 22.12 (earlier versions throw `ERR_REQUIRE_ESM`).

Credentials come from the environment, as for `Sandbox.create`: `OMEGA_BASE_URL`, and either `FI_API_KEY` plus
`FI_SECRET_KEY` or `FUTUREAGI_OMEGA_API_KEY`. To pass them in code, build the sandbox with `client.sandboxes.create`
and hand it over (`sandbox` below).

## A sandbox session (`experimental_sandbox`)

```ts
import { generateText } from "ai";
import { createFutureAGISandboxSession } from "@future-agi/sdk/sandbox/ai-sdk";

await using sandbox = await createFutureAGISandboxSession();   // creates a sandbox; deleted when the block ends

const result = await generateText({
  model,
  tools,                          // tools that use the sandbox, for example a provider's shell tool
  prompt: "Run the tests and fix what fails.",
  experimental_sandbox: sandbox,  // also streamText, ToolLoopAgent.generate and ToolLoopAgent.stream
});
```

The session is the AI SDK's `Experimental_SandboxSession`:

| Member | What it does |
|---|---|
| `run({ command, workingDirectory, env, abortSignal })` | Runs the command with `/bin/sh -c` and waits for it to end. Resolves with `{ exitCode, stdout, stderr }` for every ending (see Exit codes). |
| `readFile`, `readBinaryFile`, `readTextFile` | Read a file in `/workspace` (`readTextFile` takes `encoding`, `startLine`, `endLine`). A missing file is `null`. |
| `writeFile`, `writeBinaryFile`, `writeTextFile` | Write a file in `/workspace`, creating missing folders and replacing an existing file. Text is UTF-8. |
| `spawn` | Not offered: it rejects before anything is sent. Use `run`. |
| `description` | A line the AI SDK may add to the agent's instructions (the sandbox id, the working folder, the exit codes). |
| `sandbox` | The `Sandbox` handle, for anything else (`sandbox.snapshots`, `sandbox.hibernate()`, ...). |
| `dispose()`, `[Symbol.asyncDispose]()` | Delete the sandbox when the session owns it. |

## Tools (`sandboxTools`)

```ts
import { generateText, stepCountIs } from "ai";
import { Sandbox } from "@future-agi/sdk";
import { sandboxTools } from "@future-agi/sdk/sandbox/ai-sdk";

await using sbx = await Sandbox.create({ name: "coder" });

const result = await generateText({
  model,
  tools: { ...sandboxTools(sbx) },
  stopWhen: stepCountIs(10),
  prompt: "Write hello.py in /workspace, run it and show me the output.",
});
```

The four tools have the names, inputs and results of the Python SDK's MCP server for one sandbox (the `sandbox mcp
--sandbox ID` command), so an agent sees the same tools from either SDK:

| Tool | Input | Result |
|---|---|---|
| `sandbox_exec` | `command`, `cwd?`, `timeout_seconds?` | `exit_code`, `signal`, `timed_out`, `cancelled`, `truncated`, `duration_ms`, `error`, `exec_id`, `stdout`, `stderr`, `stdout_clipped`, `stderr_clipped` |
| `sandbox_read_file` | `path`, `max_bytes?` | `path`, `encoding` (`utf8` for text, else `base64`), `content` |
| `sandbox_write_file` | `path`, `content`, `encoding?` (`utf8` or `base64`) | `path`, `bytes` |
| `sandbox_list_files` | `path?` | `path`, `entries` (`name`, `size`, `directory`, `mode`) |

A non-zero exit, a timeout, a signal and a cancel are results the model reads; `exit_code` is `null` when a signal
ended the command or it never started. `stdout` and `stderr` keep their newest `maxOutputChars` characters (default
20000) after a first line `[... N earlier characters dropped ...]`. A refusal (a hibernated sandbox, a full quota) is
thrown, and the AI SDK hands the error to the model.

## Options

| `createFutureAGISandboxSession` | Default | |
|---|---|---|
| `sandbox` | - | An existing handle (`Sandbox.connect`, `Sandbox.create`, `client.sandboxes`). |
| `create` | `{}` | `Sandbox.create` options, used when `sandbox` is absent. Not both. |
| `workingDirectory` | `/workspace` | Where commands run and relative paths resolve. A per-call `workingDirectory` wins. |
| `timeoutSeconds` | the workspace default | Each command stops after this many seconds (at least 1). |
| `maxTimeoutSeconds` | - | The workspace's limit, `caps.exec.maxTimeoutSeconds` from `Sandbox.list()`; `timeoutSeconds` is capped to it. |
| `description` | generated | The session's `description`. |
| `deleteOnDispose` | `true` only for a sandbox the function created | Whether `dispose()` deletes the sandbox. |

`sandboxTools(sandbox, options)` takes `workingDirectory`, `timeoutSeconds` (used when the model gives none),
`maxTimeoutSeconds` and `maxOutputChars`.

## Exit codes

`run` returns a number for every ending, the same table the Python SDK's `sandbox exec` command and its
integrations use; when the code alone does not say what happened, a line is added to `stderr`.

| How the command ended | `exitCode` | Line added to `stderr` |
|---|---|---|
| its own exit code | that code | - |
| it ran past its time limit | 124 | `Command timed out after {t} seconds` |
| a signal (Linux number N) | 128 + N (137 for `SIGKILL`) | `Command was ended by signal {signal}` |
| it was cancelled | 130 | `Command was cancelled` |
| it could not start | 1 | `The command could not start: {error}` |
| no exit code and no known signal | 1 | `Command ended without an exit code` |

`run` throws only when the outcome is unknown or the request was refused: `CommandIncompleteError` (the stream ended
without an exit frame, so whether the command finished is unknown), `CommandFailedError` (the server sent an error
frame), and the request's own errors (`SandboxHibernatedError`, `QuotaExceededError`, ...). Nothing is retried: a
command that may have run is never sent again. An `abortSignal` closes the stream, which cancels the command.

## Security

- `env` passes to the command as given. It is for plain, non-secret values only: never put credentials there. The
  tools take no `env` at all.
- Credentials come only from the environment or from a client you build; never from a tool input.
- Commands and file writes appear in the sandbox's audited activity (`sandbox.activity()`).

## Hosted limits

- File calls reach `/workspace` only; read or copy anything else with a command (`cat`, `cp`).
- A file written through the session or `sandbox_write_file` goes in one request, up to the workspace's
  `caps.files.maxWriteBytes`; use `sandbox.files.upload` for larger files (its folder must exist).
- Commands stop at the workspace's `caps.exec.maxTimeoutSeconds`, and output beyond `caps.exec.maxOutputBytes` is
  dropped (`truncated`).
- A workspace runs at most `caps.maxActiveSandboxes` sandboxes at once; delete the ones you are done with.
- Outbound network access depends on the deployment; `caps.networkModes` from `Sandbox.list()` lists what it allows.

## Not offered

- `spawn` (background and streamed processes).
- Network sessions, `restricted()` and harness bridge ports.
- `stop()` as a pause: hibernate the sandbox with `sandbox.hibernate()` and `sandbox.resume()` instead.
