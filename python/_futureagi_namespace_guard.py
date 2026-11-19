"""Reject learning-kit distributions that overwrite the SDK's files.

This module intentionally lives outside ``fi``. Older learning-kit wheels ship
``fi/__init__.py`` themselves, so a check only in that initializer disappears
when those wheels are installed last. The accompanying .pth registers a lazy
finder; it does not import fi, inspect metadata or raise during Python startup.
"""

import sys


def _before_slim_release(version):
    """Compare to the fixed 0.4.0 boundary without importing dependencies.

    Distribution versions are PEP 440 metadata. Release tuples, epochs, local
    versions and pre/dev releases matter at this boundary; post releases do not
    precede their final release. Unknown version syntax is conservatively unsafe.
    """
    import re

    match = re.fullmatch(r"v?(?:(\d+)!)?(\d+(?:\.\d+)*)([^+]*)?(?:\+[^+]+)?", version.strip().lower())
    if match is None:
        return True
    epoch, release, suffix = match.groups()
    if int(epoch or 0) > 0:
        return False
    parts = tuple(int(part) for part in release.split('.'))
    parts += (0,) * max(0, 3 - len(parts))
    boundary = (0, 4, 0) + (0,) * max(0, len(parts) - 3)
    if parts != boundary:
        return parts < boundary
    return re.match(r"[._-]?(?:alpha|beta|preview|pre|rc|a|b|c|dev)(?:[._-]?\d+)?", suffix or '') is not None


def check_overlap():
    """Fail before any conflicting fi code executes; never import learning-kit."""
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        installed = distribution('agent-learning-kit')
    except PackageNotFoundError:
        return
    version = installed.version
    if _before_slim_release(version) or any(
        str(path).replace('\\', '/').startswith('fi/evals/')
        for path in (installed.files or ())
    ):
        raise ImportError(
            f'agent-learning-kit {version} ships its own copy of the fi package, '
            'which conflicts with futureagi. Upgrade agent-learning-kit to '
            '0.4.0 or later once it is available, or uninstall it; then reinstall '
            'futureagi: pip install --force-reinstall --no-deps futureagi'
        )


def _check_sdk_root():
    """Detect removal of the SDK-owned root without scanning the package tree."""
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        installed = distribution('futureagi')
    except PackageNotFoundError:
        return
    root = 'fi/__init__.py'
    if installed.locate_file(root).is_file():
        return

    # Newer Python versions filter missing paths out of Distribution.files.
    # Read the raw RECORD once, only on a missing root. Editable distributions
    # that never owned this path must not be diagnosed as a damaged wheel.
    import csv
    import io

    record = installed.read_text('RECORD')
    if record and any(row and row[0] == root for row in csv.reader(io.StringIO(record))):
        raise ImportError(
            "futureagi's files were removed, most likely by upgrading or uninstalling "
            'agent-learning-kit older than 0.4.0; reinstall futureagi: '
            'pip install --force-reinstall --no-deps futureagi'
        )


class _RootGuard:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'fi':
            _check_sdk_root()
            check_overlap()
        return None


def install():
    """Register only once, leaving normal resolution entirely unchanged."""
    if not any(isinstance(finder, _RootGuard) for finder in sys.meta_path):
        sys.meta_path.insert(0, _RootGuard())
