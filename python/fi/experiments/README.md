# `fi.experiments`: what is hidden before anything is stored (redaction)

`fi.experiments` and `futureagi-py run` / `futureagi-py upload` write a run's plan and journal to disk
(`$FI_RUN_DIR`, default `~/.futureagi/runs/<run id>/`) and, for an uploaded run, send its config, metadata,
outputs and spans to the server. Before any of that is written or sent, values that look like credentials are
replaced with `[redacted]`. This page lists exactly what is hidden. The code is
`fi/experiments/_redact.py`; `tests/experiments/unit/test_redaction_docs.py` fails when this page and the
code disagree.

**The rule fails closed (the fail-closed contract).** A name that might be a credential is hidden, even when it turns out to be
harmless config. If a value you need is hidden, rename the param (for example `max_tokens`, not `tokens`), or
pass it another way. A resume refuses `[redacted]` as a value: give the real value again.

## 1. Config keys that are credentials (params, metadata, argv, eval config)

A key's value is hidden when the key names a credential. Keys are split into words (snake_case, kebab-case,
dotted and camelCase all work), and matched as words, not substrings.

- **Always a credential**, anywhere in the key: `authorization` / `authorisation`, `secret`, `password` /
  `passwd`, `passphrase`, `credential`, `cookie`, `bearer`, `api_key` / `api-key` / `apikey`, `private_key`,
  `access_key`.
- **Any word `key` or `keys`** is a credential, also run together (`openaikey`, `azureKey`, `OPENAI_KEY`,
  `hf_key`). Not a credential:
  - English words that end in "key": donkey, donkeys, hockey, hotkey, hotkeys, jockey, lackey, monkey,
    monkeys, turkey, turkeys, turnkey, whiskey;
  - `key` / `keys` after one of these words: cache, column, composite, dedup, dedupe, dict, field, foreign,
    group, hash, idempotency, index, input, item, join, label, lookup, map, message, metadata, object, output,
    partition, primary, range, record, routing, row, shard, sort, text, unique (so `primary_key`, `sort_key`,
    `cache_key`, `input_key` stay);
  - `key` / `keys` before one of these words: column, columns, field, fields, name, names, order (so
    `key_name`, `key_order` stay);
  - a count or a limit: `key` / `keys` after max, min, n, num, total, or before count, counts, limit, limits
    (`num_keys`, `key_count`), or with max, min, num or total anywhere before it.
- **Any word `token` or `tokens`** is a credential (`token`, `access_token`, `auth_tokens`, `token_value`).
  Not a credential:
  - a count or a limit: after budget, cached, completion, input, max, min, n, num, output, prompt, reasoning,
    thinking, total, or before budget, count, counts, limit, limits, per, usage, used (`max_tokens`,
    `prompt_tokens`, `token_count`, `tokens_per_minute`), or with max, min, num or total anywhere before it
    (`max_new_tokens`, `max_output_tokens`);
  - tokenizer config: after bos, cls, end, eos, mask, pad, sep, special, start, stop, unk (`eos_token`,
    `stop_tokens`).

Under a credential key, only values that can carry a secret are hidden: strings, bytes, and every such leaf of
a dict or list. Numbers, booleans and `null` stay (`api_key_set: true`, `secret_rotation_days: 30`).

## 2. Credential assignments inside a string

Inside a string of config (an argv token, a `--param` value, an eval spec), a `NAME=VALUE` part whose name is a
credential (section 1) keeps its name and loses its value: `api_key=…`, `--token=…`, `--param=api_key=…`,
`judge:api_key=…,model=m` (only the credential's value goes), `…?token=…`. A JSON `"api_key": "…"` pair
inside a string loses its value the same way.

## 3. Values shaped like a credential, under any key of config

A string shaped like one of these has that part replaced, whatever its key:

- an `Authorization` value: `Bearer <token>` (16 or more characters, with a digit);
- OpenAI and Anthropic keys: `sk-…`, `sk-proj-…`, `sk-ant-…`;
- Groq `gsk_…`, xAI `xai-…`;
- GitHub `ghp_…` / `gho_…` / `ghu_…` / `ghs_…` / `ghr_…` and `github_pat_…`;
- an AWS access key id `AKIA…`;
- Slack `xoxa-` / `xoxb-` / `xoxp-` / `xoxo-` / `xoxs-` / `xoxr-` tokens;
- a Google API key `AIza…`;
- a Hugging Face token `hf_…`;
- a JWT (`eyJ….eyJ….…`);
- a PEM private key block (`-----BEGIN … PRIVATE KEY-----` to its end).

## 4. Secrets known to the process, everywhere

The exact values of these environment variables, when they are 8 characters or longer, are replaced wherever
they appear: in outputs, errors, span attributes, the journal and the upload.

- `FI_*`, `*_API_KEY`, `*_TOKEN`, `*_SECRET`, `*_SECRET_KEY`, `*_API_SECRET`;
- except these, which are not secrets: `FI_BASE_URL`, `FI_GRPC_URL`, `FI_JUDGE_MODEL`, `FI_LOGIN_FILE`,
  `FI_RUN_DIR`.

Outputs (the task's return value, `expected`, scores' explanations) are checked against these known values
only. They are not redacted by key or by shape, because an answer may rightly contain a word like `token`.

## 5. Where redaction applies

- the journaled `plan.json` (params, metadata, argv) and `journal.jsonl`;
- the run's `model_config` and metadata on the server, and the run name;
- the printed resume line and every command line the SDK prints for you to copy (it then names the values it
  shows as `[redacted]`);
- span attributes of an uploaded trace (`fi.experiment.param.*` and the rest).

**Your own tracer provider (`trace=<provider>`).** The run's spans then go out through your provider's exporter, not
the SDK's, so the SDK's exporter-side scrubbing does not apply to them. What the SDK writes on each trial's root span
is redacted before it is written: `input.value`, `output.value`, `fi.experiment.param.*`, and a failed trial's error
status and exception event. Spans made by your instrumentors or your own code are exported as they were made.

Your keys themselves are never journaled or uploaded: the SDK keeps them in your environment or in its own login
file (mode 0600), and never sends a provider key to the platform's key store (the dataset contract).

## 6. How failed trials and error scores are counted (`error_policy`)

This section is about the numbers, not redaction. It follows the product's run error policy (dataset service decisions after
wave 2g); `fi/experiments/results.py` is the code.

| What happened on a row | `error_policy="zero"` (the default) | `error_policy="exclude"` |
|---|---|---|
| **A failed trial**: the task raised or timed out | 0 and a fail in every evaluator's mean and pass rate | left out of every mean and pass rate; its count is shown |
| **An error score**: the evaluator raised or hit its own timeout, a judge answer held no verdict, or a provider refused the call | shown with its count and left out of that evaluator's mean and pass rate | the same |

- Both count toward `summary().error_rate`, the share of the trials that ran which failed or got an error score.
  `--max-error-rate` (`assert_passing(max_error_rate=...)`) gates on it, and under `CI=true` it defaults to 0.
- A gate (`--fail-under`, `assert_passing`) **fails for an evaluator with no scored rows**, for example a judge
  whose every answer was malformed, and its reason says why. A broken evaluator never passes a gate silently.
- The closing lines and every gate reason print both counts, and how each was counted, for example
  `graded: 0.5 < 0.75 [failed trials 1: counted as 0, a fail, in the pass rate and the mean (error policy zero, the
  default); error scores 0]`.
- `summary()` gives `failed` and `error_scores` for the run, and `failed_trials`, `errors` and `scored` for each
  evaluator. `n` is the number of scores the evaluator returned, error scores included.

Two worked examples:
- The task errors on 1 of 4 rows and the evaluator passes the other 3. The pass rate is 3 of 4 = 0.75 under `zero`
  and 3 of 3 = 1.0 under `exclude`. The error rate is 0.25 under both.
- The evaluator raises on 1 of 3 rows and passes the other 2. The pass rate is 2 of 2 = 1.0 under both policies,
  with 1 error score shown and an error rate of 1 in 3.

An uploaded run does not carry the policy, because the server's run has no error-policy field today; nothing
is sent for it.

## 7. Task timeouts and cooperative cancellation

`experiments.run(..., timeout_s=300)` and `experiments.arun(..., timeout_s=300)` (CLI `--timeout-s 300`)
bound the **task's attempts in each trial**, including user retries, transient retries and their delays.
This is one shared task budget per trial, not a fresh budget for each retry. The default is 300 seconds;
in Python, `timeout_s=None` disables this task limit. It is not a deadline for the whole run or for scoring.

**Evaluators are outside the task timeout.** They keep their own limits, such as the judge's `timeout_s`
or a provider's request timeout. An evaluator without its own bound may wait indefinitely; configure that
bound in the evaluator or its client. An evaluator timeout produces an **error score**, not a task timeout.
It does not extend or reuse the task's `timeout_s`; error scores are counted as described in section 6.

**Cancellation is cooperative.** When the runner handles a task timeout, it sets `ctx.cancelled`
(a `threading.Event` on `TaskContext`), abandons the attempt and records a timeout. The concurrency
slot is released without waiting for a synchronous task's thread to return. A synchronous task should
check `ctx.cancelled.is_set()` and stop promptly; if it ignores the event, its thread keeps running
until it returns. These abandoned threads can **exceed the concurrency setting**; there is **no forced
kill**. The runner uses daemon threads for synchronous tasks; any work a task starts in the default
executor can also keep its workers occupied until that work returns.

**Current async limitation:** cancellation can be delayed, and an async task that suppresses
cancellation can currently have its late result recorded instead of a timeout, without `ctx.cancelled`
being set. This is being fixed; do not rely on an unconditional deadline or late-result discard.

A task timeout does not stop that task's external work or undo its side effects. Ctrl-C also requests
cancellation; the cost cap only stops new trials and does not cancel one in flight.
