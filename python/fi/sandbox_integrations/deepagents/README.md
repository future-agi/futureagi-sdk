# Deep Agents backend

These integrations ship in the Future AGI SDK (`pip install futureagi`). Until that release is published, use the
sandbox HTTP API.

`FutureAGISandbox` is a [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) sandbox backend: pass it
as `backend=` to `create_deep_agent` and the agent's file and shell tools run inside a Future AGI sandbox instead of
on your machine.

## Install

```bash
pip install "futureagi[sandbox-deepagents]"
```

Python 3.11 or newer, because Deep Agents needs it. On Python 3.10 the extra installs nothing, and importing
`fi.sandbox_integrations.deepagents` raises `ImportError` saying the module needs Python 3.11+. On 3.11+ without
Deep Agents installed, the import raises `fi.errors.MissingExtraError` with the install line above.

## Authenticate

The backend uses a sandbox handle you make, so it takes the same settings as `Sandbox.create`:

- `OMEGA_BASE_URL`: the sandbox API's address (there is no default).
- `FI_API_KEY` and `FI_SECRET_KEY` (hosted), or `FUTUREAGI_OMEGA_API_KEY` (self-hosted), never both.
- `FI_WORKSPACE_ID` and `FI_ORGANIZATION_ID` when your key reaches more than one.

To pass keys in code instead, build `FutureAGIClient(...)` and use `client.sandboxes.create(...)` or
`client.sandboxes.connect(id)`; they return the same handle. Never put a key in a command or its `env`.

## Quickstart

```python
from deepagents import create_deep_agent
from fi.sandbox import Sandbox
from fi.sandbox_integrations.deepagents import FutureAGISandbox

with Sandbox.create(name="agent-scratch") as sbx:          # deleted when the block ends
    agent = create_deep_agent(model="...", backend=FutureAGISandbox(sandbox=sbx))
    agent.invoke({"messages": [{"role": "user", "content": "write and run a test"}]})
```

`FutureAGISandbox(sandbox=sbx, workdir="/workspace", timeout=None, max_timeout=None)`:

| Argument | Meaning |
|---|---|
| `sandbox` | A sync `fi.sandbox.Sandbox` handle. `AsyncSandbox` is not supported yet (async agents work: Deep Agents runs the backend in worker threads). |
| `workdir` | The folder commands run in. Default `/workspace`. |
| `timeout` | The default time limit of a command, in seconds. Default 30 minutes, or your workspace's maximum when that is lower. |
| `max_timeout` | Your workspace's exec maximum, in seconds (`caps.exec.maxTimeoutSeconds` of its sandbox settings). Default: read from the settings. |

Building the backend makes two requests: it reads your workspace's sandbox settings for the exec time limit (not
when you pass `max_timeout`), and runs `command -v python3` in `workdir`. Deep Agents runs `python3` inside the
sandbox for `ls`, `read_file`, `edit_file` and `glob`, so a sandbox without it is refused with `ConfigurationError` (code `python3_missing`).
Every catalog template ships `python3`; an image of your own must have it on its `PATH`.

## What the agent can do

The agent gets Deep Agents' sandbox tools: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep` and
`execute`. Deep Agents builds all of them on three backend calls:

- `execute(command, *, timeout=None)` runs a shell command in `workdir`, once.
- `upload_files(files)` writes files, creating each file's folder first.
- `download_files(paths)` reads files as bytes.

Inside the sandbox, commands run as an unprivileged user (uid 1000). `/workspace` and `/tmp` are writable; the
rest of the filesystem is read-only.

`upload_files` and `download_files` use the sandbox's files API, whose paths are relative to `/workspace`. They
reach files under `/workspace` only: `/workspace/src/app.py` is sent as `src/app.py`, and a path elsewhere
(`/tmp/x`, `/etc/hosts`) gets `permission_denied` without a request. So `write_file` works under `/workspace` only
(a `write_file` to `/tmp` creates its folder, then fails with `permission_denied`), while `ls`, `read_file`,
`glob`, `grep`, `delete` and small edits run through `execute` and work anywhere the sandbox user may read or
write. An `edit_file` whose old and new text together pass 50,000 bytes fails anywhere, even under `/workspace`,
because Deep Agents stages it in `/tmp` through `upload_files`. Keep the agent's files under `/workspace`.

## Timeouts and exit codes

The workspace's exec maximum is an operator setting, read when you build the backend unless you pass
`max_timeout` (`backend.max_timeout`). A `timeout` of 0, or anything above the maximum, means the maximum: sandboxes
have no unlimited run. With no `timeout`, a command gets `backend.timeout`.

`ExecuteResponse.exit_code` is the code `futureagi-py sandbox exec` exits with:

| How the command ended | `exit_code` | Note added to `output` |
|---|---|---|
| It exited | its own code | none |
| It ran past its time limit | 124 | `Command timed out after {t} seconds` |
| Signal N ended it (Linux numbering) | 128 + N (`SIGKILL` is 137) | `Command was ended by signal {signal}` |
| It was cancelled | 130 | `Command was cancelled` |
| It could not start | 1 | `The command could not start: {error}` |
| A signal with no known number, or no code at all | None | `Command ended without an exit code ({signal})` |

`output` is stdout, then `<stderr>...</stderr>` on a new line when the command wrote to stderr, then the note on
its own line. `truncated` is True when output beyond the server's cap was dropped. A timeout returns the output
read until then; the command is not run again.

## Hosted limits

Hosted sandboxes have no internet access today, so `pip install` or `npm install` inside a hosted sandbox fails.
Create the sandbox from a template that already has what the agent needs (`Sandbox.list().caps` lists the
templates). A file upload is limited to 64 MiB on hosted.

## Lifecycle

You create and delete the sandbox; the backend never does. `with Sandbox.create(...) as sbx:` deletes it when the
block ends. Nothing resumes a hibernated sandbox for you: building a backend on one raises the handle's
`SandboxHibernatedError`, and a command or file call on a sandbox that hibernated later answers with an error that
says to resume it (`sbx.resume()`).

## Errors

`execute` returns a result for every way a command can end, and for a failed call too:

| What happened | `output` | `exit_code` |
|---|---|---|
| The connection ended before the exit record | what arrived, then `Error: the connection ended before the command finished; whether it finished is unknown` | None |
| The server failed after the command started | what arrived, then `Error executing command (CommandFailedError): {message}` | 1 |
| The sandbox is hibernated | `Error: sandbox {id} is hibernated; resume it (sbx.resume()) before running commands` | 1 |
| Any other refusal (rate limit, permission, server error) | `Error executing command ({error class}): {code}: {message}` | 1 |

Nothing is retried: a command whose outcome is unknown is never run again, and each file is uploaded once.

`upload_files` and `download_files` report a failure on that file and go on with the others:

| Refusal | Error |
|---|---|
| A relative path | `invalid_path` (nothing sent) |
| A path outside `/workspace` | `permission_denied` (nothing sent) |
| Not found (404) | `file_not_found` |
| Forbidden (403), a folder the sandbox can't write, a read-only sandbox | `permission_denied` |
| A folder where a file was expected | `is_directory` |
| Over the upload cap (413) | `file_too_large` |
| Any other refusal (400) | `invalid_path` |
| Anything else | `{code}: {message}` |

A setup problem (no `OMEGA_BASE_URL`, both kinds of credential) raises `fi.sandbox.ConfigurationError` from every
call, so an agent does not retry a call that cannot work.

## Coming from `langchain-e2b` or `langchain-daytona`

- The constructor takes the handle by keyword, as theirs do: `FutureAGISandbox(sandbox=sbx)`. Lifecycle stays
  with you in all three.
- The default `workdir` is `/workspace` (E2B uses `/home/user`).
- stderr is tagged `<stderr>...</stderr>`, as Daytona and LangChain's backend template do; E2B joins it with a
  newline.
- A timeout gives exit code 124 in all three. `timeout=0` means "wait without limit" on Daytona and the workspace's
  maximum here.
- Building the backend checks for `python3` up front instead of failing on the first file tool.

## Not yet

- `edit_file` with old and new text over 50,000 bytes together, and `write_file` outside `/workspace`: both
  upload to paths the files API does not reach (Deep Agents stages large edits in `/tmp`).
- An async class over `AsyncSandbox`.
- A `dcode --sandbox futureagi` provider for Deep Agents Code.
- A listing in LangChain's integrations directory.

The module path `fi.sandbox_integrations.deepagents`, the class name `FutureAGISandbox` and the extra
`sandbox-deepagents` are provisional names and may change before the first release that includes them.
