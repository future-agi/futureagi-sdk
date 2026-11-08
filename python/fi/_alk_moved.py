"""Clear ImportErrors for code that moved from agent-learning-kit's old layout to ``fi.alk``.

The SDK owns the rest of ``fi.*``; agent-learning-kit owns ``fi.alk``. Nothing here imports,
installs, wraps or re-exports ALK. The distribution name lives in one constant so a later
rename of the install name is a single edit.
"""

ALK_DISTRIBUTION = "agent-learning-kit"
ALK_LAST_FI_LAYOUT_VERSION = "0.3.4"


def _moved(old: str) -> str:
    return f"{old} belonged to {ALK_DISTRIBUTION} {ALK_LAST_FI_LAYOUT_VERSION} and moved to the separate fi.alk package."


def namespace_moved(old: str, new: str) -> ImportError:
    """For a whole former namespace such as ``fi.simulate``, raised by its package ``__init__``."""
    return ImportError(
        f"{_moved(old)} Use {new} instead of {old}; {old}.X -> {new}.X. "
        "Underscore-prefixed (private) modules have no public replacement. "
        f"Install {ALK_DISTRIBUTION} and import from fi.alk."
    )


def module_moved(old: str, new: str) -> ImportError:
    """For one former module that the SDK does not provide."""
    return ImportError(f"{_moved(old)} Install {ALK_DISTRIBUTION} and import {new} instead.")


def name_moved(module: str, name: str, replacement: str) -> ImportError:
    """For one former name in an SDK module that keeps its own API."""
    return ImportError(
        f"{_moved(f'{module}.{name}')} Install {ALK_DISTRIBUTION} and use `{replacement}` instead. "
        "fi.evals keeps the futureagi SDK API."
    )
