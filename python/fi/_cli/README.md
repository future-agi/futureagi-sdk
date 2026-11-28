# The `futureagi-py` CLI and its command-group registry

There is one `futureagi-py` binary for the whole platform. The core (`fi/_cli/`) owns the entry point
(`main.py`, with the exit-code table), the registry (`registry.py`), `doctor` (`doctor.py`) and
`login` / `logout` (`auth.py`: one saved login, read by `fi._credentials` for every module).
Every other command is a **group** that registers itself.

## Add a command group

1. Write a module with `register(subparsers) -> None`. Import only `argparse` at module level, so
   `futureagi-py --help` stays fast and a missing optional dependency cannot break other commands.
   Give every command `help=`: it is the text `futureagi-py --help` shows (a command without one is
   listed with no text; `help=argparse.SUPPRESS` hides it; aliases are listed after the name):

   This illustrative plugin is not a built-in SDK command:

   ```python
   # example_commands.py
   import argparse

   def register(subparsers) -> None:
       p = subparsers.add_parser("example", help="an example plugin")
       p.add_argument("--json", action="store_true")
       p.set_defaults(func=_run)

   def _run(args) -> int:
       # Import the plugin's dependencies here, not at module level.
       print('{}' if args.json else 'Example plugin loaded')
       return 0
   ```

2. Add one line to the distribution's `pyproject.toml`:

   ```toml
   [tool.poetry.plugins."futureagi.cli"]
   example = "example_commands"
   ```

   Another distribution can add a group the same way.

3. Optional: add a `futureagi-py doctor` section with
   `fi._cli.doctor.add_section("example", lambda args: ["line", ...])` inside `register()`.
   If the section reads its own arguments, add them to `doctor` with
   `fi._cli.doctor.add_argument(subparsers, "--example-id", help=...)`, passing the same
   `subparsers` your `register()` received (it does nothing when that parser has no `doctor`, as
   in a unit test that registers one group on a bare parser). Doctor's arguments are **one
   namespace shared by every group**:
   - an argument whose `dest` is already there is left alone, so two groups that add the same
     flag share one value. Name your flags for your group (`--example-id`, not `--name`);
   - only one positional fits, and the experiments group already adds `TARGET`. Use flags.

   `futureagi-py doctor --json` prints one object: the local checks (`server`, `keys`, `platform`,
   `login`, `python`, `note`) and `sections` (each title to `{"lines": [...]}` or
   `{"error": "..."}`). A section's lines are the same in both forms.

4. Optional: hooks, added inside `register()` (the core imports no group, so anything only your
   group knows reaches it this way):

   ```python
   from fi._cli import registry

   registry.add_pre_parse(fn)      # fn(argv) -> int | None: see the raw argv first; an int ends the command
   registry.add_on_interrupt(fn)   # fn(exc, argv) -> str | None: what Ctrl-C prints (default "Interrupted.")
   registry.add_on_exit(fn)        # fn(code): after the command, in the console script only
   ```

5. Put each command in a `--help` section: `registry.set_section("example", "platform")`.
   The sections are Evaluate, Platform and Setup. Only registered commands appear.

6. Optional: set `install_hint` on your parser to an install command for a real extra owned
   by your plugin's distribution. A `ModuleNotFoundError` that escapes your handler then
   prints `error: <...>. Run: <hint>` and exits 3. Alternatively, raise
   `fi.errors.MissingExtraError(extra="<your-extra>", module="...")` yourself. Without either, the core names the missing module (not a guessed `pip install`
   line: an import name is not a distribution name). Any other `ImportError` (an installed package
   that fails to import) prints one `IMPORT_FAILED` line with no install hint, and exits 3.

## Rules

- A handler returns an int exit code. Raise an `SDKException` subclass with an `exit_code`
  attribute for failures; `main.py` prints `error: <message>` (or the `--json` error object).
- Every command takes `--json`, `doctor` included.
- Exit codes: 0 ok · 1 a gate failed · 2 usage error · 3 setup/server/missing extra ·
  4 interrupted · 5 trial errors above `--max-error-rate`.
- Credentials come from `fi/_credentials.py` (arguments, environment, one saved login bound to
  its base URL). Read keys only that way.
- Errors come from `fi.errors` (`TransportError`, `MissingExtraError`, the API status classes) or
  subclass it. An `httpx.TransportError` that escapes a handler prints one line and exits 3:
  `cannot reach ...; check FI_BASE_URL` when nothing was sent, `... did not answer in time` for a
  timeout after connecting, `the connection to ... broke` for a reset.
- A group whose `register()` raises, or a hook that raises, is skipped with one warning naming
  it; every other command works. `tests/test_cli_core.py` shows the cases with fake entry
  points.
- In a source checkout (no installed metadata), the registry reads the `futureagi.cli` table from
  `python/pyproject.toml`, so a group works there as soon as its line is in the table.

## The `sandbox` group and the exec channel

`futureagi-py sandbox` (`sandbox.py`) is a group like any other; its commands that ride the sandbox
exec channel (a WebSocket, `fi.sandbox`'s `commands.exec_stream`) keep their work in
`sandbox_channel.py`, which `sandbox.py` imports only when one of them runs:

| Command | What it does |
|---|---|
| `sandbox rsh ID [--] COMMAND...` | Runs the command with local standard input, output and error joined to it byte for byte; exits with the command's code (130 on Ctrl-C). The transport rsync and scp run. |
| `sandbox ssh ID` | An interactive shell: `/bin/sh -i`, or the `shell` the sandbox's record reports. The local terminal is raw while it runs and is restored on every exit. |
| `sandbox rsync ID ARGS...` | Runs the system `rsync` with `-e "<this CLI> sandbox rsh ID"`. Write the sandbox side as `:path`. |
| `sandbox scp ID ARGS...` | Runs the system `scp` (classic protocol, `-O`) with `-S` naming a wrapper that maps to `rsh`. `:path` is the sandbox side. |

`ssh` is the one place that joins a terminal to a shell (`open_shell` in `sandbox_channel.py`). The
server serves exec streams only, so the shell has no remote terminal: this side puts the terminal in
raw mode and does the echo and line editing. When the server offers PTY streams, `open_shell` is where
to attach one and drop the line editor.

A close from the server (4401 access revoked, 4404 sandbox gone, 4409 emergency stop, 4410 hibernated,
4411 frozen, 1001 server stopping) ends the command with a message and exit code 1. A 404 from the
token route means the operator switched the channel off.

The channel sends no keepalive pings: the server defers its pongs while this side owes output credit
(a slow `rsync` writing to a slow disk), and a ping timeout would close that connection with 1011.
The connection is also kept out of DEBUG logs of `websockets`, whose handshake lines hold the
single-use data token (`Sec-WebSocket-Protocol`): the channel uses its own logger, named
`fi.sandbox.channel.websocket`, at INFO and above.

Names a group adds to the CLI are also listed in `RESERVED_NAMES` of
`scripts/packaging/rename-cli.py`, so a renamed program keeps them.
