"""Keep server defaults opt-in in the generated Python SDK model.

The API documents ``include_trial_stability`` as a server-side default of
false. The Python SDK should omit the optional key unless a caller explicitly
chooses true or false, so adding this response projection cannot change an
existing request body. This post-hook is deliberately narrow and rerunnable.
"""

from __future__ import annotations

from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: preserve-sdk-optional-defaults.py MODEL")
    path = Path(sys.argv[1])
    source = path.read_text()
    old = "    include_trial_stability: bool | Unset = False\n"
    new = "    include_trial_stability: bool | Unset = UNSET\n"
    if new in source or "include_trial_stability" not in source:
        return
    if source.count(old) != 1:
        raise ValueError(f"expected one generated trial-stability default in {path}")
    source = source.replace(old, new).replace(
        "include_trial_stability (bool | Unset):  Default: False.",
        "include_trial_stability (bool | Unset): Omitted unless set. Server default: False.",
    )
    path.write_text(source)


if __name__ == "__main__":
    main()
