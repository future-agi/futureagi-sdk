"""Clear ImportErrors for code that moved from agent-learning-kit's old layout to ``fi.alk``.

The SDK owns the rest of ``fi.*``; agent-learning-kit owns ``fi.alk``. Nothing here imports,
installs, wraps or re-exports ALK. The distribution name lives in one constant so a later
rename of the install name is a single edit.
"""

ALK_DISTRIBUTION = "agent-learning-kit"
ALK_LAST_FI_LAYOUT_VERSION = "0.3.4"


class _NamespaceFallback:
    """Give guidance only after every real finder has declined the name."""

    _targets = {'fi.opt': 'fi.alk.optimize', 'fi.simulate': 'fi.alk.simulate'}

    def find_spec(self, fullname, path=None, target=None):
        replacement = self._targets.get(fullname)
        if replacement is None:
            return None
        import sys
        from importlib.util import spec_from_loader

        # Usually this finder is last. Providers (including editable installs)
        # can append finders later, so consult those as well before giving up.
        following = False
        for finder in tuple(sys.meta_path):
            if finder is self:
                following = True
                continue
            if not following:
                continue
            find_spec = getattr(finder, 'find_spec', None)
            if find_spec is not None:
                spec = find_spec(fullname, path, target)
            else:
                # Python 3.10/3.11 still permit legacy meta path finders.
                loader = finder.find_module(fullname, path)
                spec = spec_from_loader(fullname, loader) if loader is not None else None
            if spec is not None:
                return spec
        raise namespace_moved(fullname, replacement)


def install_namespace_fallback():
    """Register without replacing sys.meta_path or intercepting real packages."""
    import sys

    if not any(isinstance(finder, _NamespaceFallback) for finder in sys.meta_path):
        sys.meta_path.append(_NamespaceFallback())


def _moved(old: str) -> str:
    return f"{old} belonged to {ALK_DISTRIBUTION} {ALK_LAST_FI_LAYOUT_VERSION} and moved to the separate fi.alk package."


def namespace_moved(old: str, new: str) -> ImportError:
    """For a former namespace that no installed provider can resolve."""
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
