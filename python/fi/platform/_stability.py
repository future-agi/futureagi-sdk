from __future__ import annotations

import warnings


class BetaWarning(UserWarning):
    """Raised (as a warning) when calling a beta method."""


_warned: set[str] = set()


def _stability(op_id: str, stability: str) -> None:
    if op_id in _warned:
        return
    _warned.add(op_id)
    if stability == "beta":
        warnings.warn(f"{op_id} is in beta and may change without notice.", BetaWarning, stacklevel=3)
    elif stability == "deprecated":
        warnings.warn(f"{op_id} is deprecated.", DeprecationWarning, stacklevel=3)
