"""A comparison's label must describe the two recordings it compares.

The label ``<golden>-><new>`` picks which intended-difference rules apply, so a
wrong label applies the wrong rules: comparing a port with 1.0.0 under the
label ``ts-client-1.0.0-esm->ts-client-1.0.1-esm`` would let D-01 (proven only
between the two fixed goldens) cover it. ``label_problems`` says why a label
does not fit; ``compare.compare`` refuses such a label. The rules:

- the golden side is a golden in catalog.json, and ``--golden`` is that
  committed golden byte for byte (its directory name included);
- the new side is either a golden, and then ``--new`` is that golden byte for
  byte (a fresh re-recording is: two recordings are byte-identical), or a new
  recording named in catalog.json ``comparisons.new_recordings``, judged only
  against one of the baselines listed for it.

The TypeScript twin is gateway-client/tests/parity/labels.mjs.
"""

from __future__ import annotations

import json
from pathlib import Path


class LabelError(ValueError):
    """A label that does not describe the comparison it names."""


def same_recording(a: Path, b: Path) -> bool:
    """Whether recording ``a`` is recording ``b`` byte for byte: index.json and every area file."""
    try:
        index = (b / "index.json").read_bytes()
        if (a / "index.json").read_bytes() != index:
            return False
        names = json.loads(index).get("files", {})
        return all((a / n).read_bytes() == (b / n).read_bytes() for n in names)
    except (OSError, ValueError):
        return False


def label_problems(
    label: str, golden_dir: Path, new_dir: Path, golden_root: Path | None = None
) -> list[str]:
    """Why ``label`` does not name the comparison of ``golden_dir`` with ``new_dir``."""
    from ._fixtures import GOLDEN, load

    root = golden_root or GOLDEN
    catalog = load("catalog.json")
    goldens = set(catalog["goldens"])
    baselines = catalog["comparisons"]["new_recordings"]
    old, sep, new = label.partition("->")
    if not sep or not old or not new or "->" in new:
        return [f"label {label!r} is not <golden>-><new>"]
    out = []
    if old not in goldens:
        out.append(f"{old!r} is not a golden ({', '.join(sorted(goldens))})")
    elif Path(golden_dir).name != old or not same_recording(
        Path(golden_dir), root / old
    ):
        out.append(f"--golden {golden_dir} is not the committed golden {old}")
    if new in goldens:
        if not same_recording(Path(new_dir), root / new):
            out.append(
                f"the new side {new!r} names a golden, so --new must be that golden "
                f"byte for byte, and {new_dir} is not"
            )
    elif new not in baselines:
        out.append(
            f"the new side {new!r} is neither a golden nor a new recording named in "
            f"catalog.json comparisons ({', '.join(sorted(baselines))})"
        )
    elif old in goldens and old not in baselines[new]:
        out.append(f"{new} is judged against {' or '.join(baselines[new])}, not {old}")
    return out


def check_label(label: str, golden_dir: Path, new_dir: Path) -> None:
    problems = label_problems(label, golden_dir, new_dir)
    if problems:
        raise LabelError(f"label {label!r} refused: " + "; ".join(problems))
