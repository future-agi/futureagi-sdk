# `fi.experiments.sandbox`: one sandbox per trial, the results in an experiment run

This ships in the Future AGI SDK (`pip install futureagi`). Until that release is published, use the sandbox
HTTP API.

`run_in_sandboxes(dataset, spec, evaluators)` runs every (row, trial) of a dataset in its own sandbox: it writes
the row and your task files, runs the agent, runs a verifier, reads a reward, and deletes the sandbox, even when
the trial fails or you press Ctrl-C. The results are an ordinary `fi.experiments` run: the same trials,
concurrency, timeouts, journal, resume and upload, the same experiment views. Nothing here is a second engine.

```python
from fi.experiments.sandbox import SandboxEval, reward, run_in_sandboxes

async def agent(row, sbx, ctx):            # sbx is an AsyncSandbox; ctx is the trial's TaskContext
    answer = await my_model(row["instruction"])          # your model call, in this process
    await sbx.files.write("/workspace/answer.py", answer)
    return {"answer": answer}

spec = SandboxEval(agent=agent, verifier="python3 /workspace/tests/check.py")
result = run_in_sandboxes("swe-mini", spec, [reward()], trials=2, name="sandbox-run")
```

Names in this module (`fi.experiments.sandbox`, `SandboxEval`, `run_in_sandboxes`, `sandbox_task`, `reward`)
are provisional until the owner names them.

## 1. When to use it

- The task changes files or runs code, and the score comes from running a check (tests, a script, a linter).
- Trials must not see each other's files: each one starts from a fresh sandbox.
- You already use `fi.experiments` and want the same run, gate and upload, with the work done in a sandbox.

For a task that only calls a model and returns text, use `fi.experiments.run` directly.

## 2. Two modes: the agent outside (hosted) or inside

**Agent outside** (`agent=`): your async function `agent(row, sbx, ctx)` runs in this process, calls your model,
and acts on the sandbox through the handle (`sbx.files`, `sbx.commands`). Only the verifier runs inside. This is
the mode for hosted sandboxes: hosted sandboxes have no network today; the owner ruled full internet (G-05), being
built. Until it ships, a command inside a hosted sandbox cannot reach a model API.

**Agent inside** (`agent_command=`): a command, such as `python3 /workspace/solve.py /workspace/task.md`, runs
inside the sandbox. Use it on a self-hosted deployment whose sandboxes have network, or for an agent that needs
none.

Exactly one of the two is set.

## 3. `SandboxEval` fields

| Field | Default | Meaning |
|---|---|---|
| `agent_command` | None | the agent as a command inside the sandbox, or `lambda row: "..."` |
| `agent` | None | `async def agent(row, sbx, ctx)`, run here; its return value is the output's `agent.result` |
| `verifier` | None | a command (or `lambda row: "..."`) run after the agent |
| `files` | None | `{absolute path: text or bytes}`, or `lambda row: {...}`, written before the agent |
| `env` | None | plain, non-secret variables for both commands, or `lambda row, ctx: {...}` |
| `template`, `size`, `image` | the workspace's defaults | passed to the create |
| `cwd` | `/workspace` | the commands' folder |
| `agent_timeout_s` / `verifier_timeout_s` | 900 / 300 | each command's own limit (at least 1; at most the workspace's `caps.exec.maxTimeoutSeconds`) |
| `reward_path` | `/workspace/.fi-eval/reward` | where the verifier writes the reward |
| `reward_from_exit` | True | without a reward file: 1.0 when the last command exited 0, else 0.0 |
| `trace_env` | True | pass `TRACEPARENT` / `TRACESTATE` to the commands (section 8) |
| `name_prefix` | `fi-eval` | the start of every sandbox name |
| `max_output_chars` | 20000 | how much of each command's stdout and stderr the output keeps (the end) |

A wrong field is refused when the `SandboxEval` is made (`fi.experiments.errors.UsageError`), before any sandbox
exists. A timeout above the workspace's longest command is refused before the first create
(`fi.sandbox.ConfigurationError`, code `timeout_above_cap`).

## 4. One trial

1. **Slot.** The trial waits for one of `max_active` slots and keeps it until its sandbox's delete returns.
2. **Create.** `AsyncSandbox.create(name=f"{name_prefix}-{batch_id}-{example_id}-{trial}", template=, size=,
   image=)`; the name is cut to 63 characters (and 120 bytes).
3. **Setup.** `/workspace/.fi-eval/row.json` (the row: `id`, `number`, `data`, `inputs`, `expected`,
   `metadata`), then each `files` entry. A write creates missing parent folders. All of it is written before
   the agent runs, so an agent command can read every field of `row.json`, `expected` included, and can read
   and change every `files` entry, test files included, before the verifier runs: the agent and the verifier
   share one filesystem. Keep the answer out of the row and the files if an agent command must not see it. With
   `agent=`, your function already holds `row` and decides what the model sees, and it can write the test files
   itself after the model's last action, so the model never sees them.
4. **Agent.** The command, with `env` plus `EVAL_ROW_FILE`, `EVAL_EXAMPLE_ID`, `EVAL_TRIAL` and `EVAL_RUN_ID`;
   or your function.
5. **Verify.** The reward file is removed (a file the agent left there does not count), then the verifier
   command runs, with the same env. Then the reward file is read.
6. **Delete.** Always, in `finally`. A failed delete is recorded (`deleted: false`, `delete_error`) and the
   sandbox is left for the sweep (section 6).

The output the run records for the trial:

```json
{"sandbox_id": "sbx_...", "deleted": true,
 "agent": {"exit_code": 0, "shell_exit_code": 0, "timed_out": false, "signal": null, "cancelled": false,
           "truncated": false, "duration_ms": 41230, "stdout_tail": "...", "stderr_tail": "..."},
 "verifier": {"exit_code": 0, "shell_exit_code": 0, "...": "..."},
 "rewards": {"reward": 1.0},
 "phases_ms": {"create": 900, "setup": 120, "agent": 41230, "verify": 3100, "delete": 400}}
```

With `agent=`, `"agent"` is `{"result": <what your function returned>}`. `shell_exit_code` is the SDK's one
exit-code table: the exit code, 124 for a timeout, 128 + N for signal N, 130 for a cancel, 1 for a command that
could not start. No env value and no key is ever in the output.

**Failures.** A trial whose create was refused after the quota wait, whose agent raised, or whose command stream
ended without an exit record fails, after its sandbox is deleted; the run counts it under its `error_policy`. A
verifier that exits non-zero is not a failure: it is a reward of 0. No command or write is sent twice, and a
create is sent again only after a quota refusal (section 6). After a sandbox error (`fi.sandbox.SandboxError`)
that the engine would count as transient, such as a 503 or a lost connection, the trial is recorded as failed
and the engine does not run it again (`Limits(retries=N)` still runs it again, in a new sandbox, when you ask for
that). Any other error, such as a 429 or 5xx from your own model call in `agent=`, keeps the engine's normal
handling: its backoff, its concurrency halving on a 429, and a new run of the whole trial, in a new sandbox.

## 5. The reward file

The verifier writes `/workspace/.fi-eval/reward` (or `reward_path`):

- one number (`1`, `0.5`) gives `{"reward": n}`;
- a JSON object of numbers (`{"reward": 1, "style": 0.5}`) gives each one;
- anything else gives no rewards and a `reward_error` in the output;
- no file: with `reward_from_exit`, 1.0 when the verifier (or, without one, the agent command) exited 0.

With a verifier, the file is removed just before the verifier runs, so a reward the agent wrote there is never
read: only the verifier's own file, or its exit code, counts. Without a verifier, the agent's file is the reward.

`reward(key="reward", passing_score=1.0)` is a local evaluator that scores `output["rewards"][key]`; a trial with
no such reward gets an error score. Use one per key: `[reward(), reward("style", passing_score=0.5)]`.

## 6. Caps, the quota wait and cleanup

- **Sandboxes at once.** `max_active=` if you give it, else the workspace's `caps.maxActiveSandboxes` (read once
  from the sandbox settings), else 2. The engine's `concurrency` is lowered to it. A hosted workspace allows 2.
  An organization's own limit is not readable yet; a create over it gets the same quota refusal and waits.
- **The quota wait.** A create refused with 409 `quota_exceeded` created nothing, so it is sent again after the
  server's `Retry-After` (else 5 s), until `quota_wait_s` (default 120; 0 turns the wait off) is spent. No other
  call is sent again. A create that got no answer is never repeated: whether it made a sandbox is unknown.
- **Task timeout.** Unless you pass `timeout_s`, the run's task limit is `agent_timeout_s + verifier_timeout_s +
  quota_wait_s + 120` seconds. When it passes, the trial is cancelled, the running command is cancelled with it,
  and the sandbox is still deleted.
- **The sweep.** After the run, in `finally`, `run_in_sandboxes` lists the workspace's sandboxes and deletes every
  one of this batch (its name starts with `{name_prefix}-{batch_id}-`) that is still there, printing one stderr
  line for each. That covers a create whose answer was lost and a delete that failed. If you call
  `fi.experiments.run(dataset, sandbox_task(spec), ...)` yourself, run `await task.sweep()` after it.
- **Under `futureagi-py run`.** In a run file the CLI loads, `run_in_sandboxes` only declares the run and the CLI
  runs it, so two things differ. No sweep follows the run: one stderr line at load time names the batch, and
  `asyncio.run(sandbox_task(spec, batch_id="<that id>").sweep())` (with the same `client_factory=`, if you used
  one) deletes its leftovers afterwards. And
  `concurrency` is lowered only to a `max_active=` you pass (the settings are not read at load time), while a
  `--concurrency` flag replaces it: pass `max_active=` and keep `--concurrency` at or below it, or trials wait
  for a slot inside their own `timeout_s`.

## 7. Where the sandboxes come from

By default, from the environment, as `fi.sandbox.AsyncSandbox`: `OMEGA_BASE_URL`, then `FI_API_KEY` +
`FI_SECRET_KEY` (hosted) or `FUTUREAGI_OMEGA_API_KEY` (self-hosted), and `FI_WORKSPACE_ID` /
`FI_ORGANIZATION_ID`. To pass them in code, give `client_factory=`: a function (sync or async) that builds an
`AsyncFutureAGIClient` (or returns its `.sandboxes`). It is called inside the loop that uses it, because `run()`
drives a private loop on its own thread and a client must not cross loops; a client it builds is closed after use.

`env=` is for plain, non-secret variables: the values go to the sandbox's runtime in clear. The names
`FI_API_KEY`, `FI_SECRET_KEY`, `FUTUREAGI_OMEGA_API_KEY`, `FI_PLATFORM_TOKEN` and `OMEGA_OS_API_KEY` are refused
(`fi.sandbox.ConfigurationError`, code `secret_in_env`). The names this module adds start with `EVAL_`, not `FI_`.

## 8. Tracing

When the run traces (`trace=True`, or your provider), each trial gets child spans `sandbox.create`,
`sandbox.setup`, `sandbox.agent`, `sandbox.verify` and `sandbox.delete` under its root span, exported with the
rest of the trial. They carry the sandbox id and the commands' `shell_exit_code`, never env values. They are
stored where the run's traces are: the Observe project of the run, joined to the run by run id. With your own
provider, the phase spans go through the global tracer provider, so set yours as the global one.

With `trace_env=True`, the agent and verifier commands get `TRACEPARENT` / `TRACESTATE` for their phase span, so
code inside the sandbox that has its own OpenTelemetry can join the trial's trace. Sending spans from inside a
sandbox needs keys and network there, which this module does not pass.

## 9. Results

A run looks like any other `fi.experiments` run: one item per (row, trial) with the output above, its error, its
latency and its scores; `reward()` scores are the run's metrics. Token counts and cost come from the engine's span
accounting and `ctx.add_cost(usd)` in your agent, not from the sandbox.

## 10. Coming from Harbor

| Harbor | Here |
|---|---|
| `instruction.md` | `files={"/workspace/instruction.md": ...}` (or a function of the row) |
| `tests/test.sh` (copied in at verification time) | `files` for the test files, `verifier="bash /workspace/tests/test.sh"`; unlike Harbor, `files` are written before the agent runs, so the agent can read and change them (section 4) |
| `/logs/verifier/reward.txt` | `/workspace/.fi-eval/reward` (the root filesystem is read-only; `/workspace` is writable) |
| an experiment per job, a run per trial, a child run per phase, feedback per reward key | the run, its trials, the phase spans, `reward(key)` |

Each task does not build its own image: pick a `template` or an allowed `image`.
