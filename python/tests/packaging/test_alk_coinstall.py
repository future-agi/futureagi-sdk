"""Offline ownership and install-order checks for the slim learning-kit boundary.

Set SDK_TEST_WHEEL to an archive-built SDK wheel and ALK_TEST_WHEELS to the
published agent-learning-kit 0.3.7 wheel. Missing artifacts are explicit skips,
not certification. The slim 0.4.0 wheel is deliberately a test double, not a
claim about a published release. Rejection needs no runtime dependencies and
must precede imports from the conflicting distribution. Recovery probes use the
test runner's installed dependencies only after validating the repaired SDK's
isolated package path, so they can exercise the real Client export offline.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import zipfile

import pytest


PYTHON_ROOT = Path(__file__).resolve().parents[2]
ORDERS = [("sdk", "alk"), ("alk", "sdk")]
OFFLINE = """
import sys
def offline(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn'}:
        raise AssertionError('Import attempted forbidden I/O: ' + event)
sys.addaudithook(offline)
"""


def record_paths(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        records = [name for name in archive.namelist() if name.endswith('.dist-info/RECORD')]
        assert len(records) == 1
        return {row[0] for row in csv.reader(io.StringIO(archive.read(records[0]).decode())) if row}


def make_wheel(root: Path, name: str, version: str, files: dict[str, str]) -> Path:
    """Write a minimal standards-compliant wheel with real RECORD digests."""
    stem = name.replace('-', '_') + '-' + version
    info = stem + '.dist-info'
    contents = dict(files)
    contents[info + '/METADATA'] = f'Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n'
    contents[info + '/WHEEL'] = 'Wheel-Version: 1.0\nGenerator: test-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
    record = io.StringIO(newline='')
    rows = csv.writer(record, lineterminator='\n')
    wheel = root / (stem + '-py3-none-any.whl')
    with zipfile.ZipFile(wheel, 'x') as archive:
        for path, content in contents.items():
            data = content.encode()
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            archive.writestr(path, data)
            rows.writerow((path, 'sha256=' + digest, len(data)))
        rows.writerow((info + '/RECORD', '', ''))
        archive.writestr(info + '/RECORD', record.getvalue())
    return wheel


@pytest.fixture
def sdk_wheel():
    value = os.environ.get('SDK_TEST_WHEEL')
    if not value:
        pytest.skip('SDK_TEST_WHEEL must name an archive-built candidate wheel')
    return Path(value).resolve(strict=True)


@pytest.fixture
def fat_wheel():
    value = os.environ.get('ALK_TEST_WHEELS')
    if not value:
        pytest.skip('ALK_TEST_WHEELS must name the published 0.3.7 wheel')
    wheels = [Path(path).resolve(strict=True) for path in value.split(os.pathsep)]
    matches = [path for path in wheels if path.name == 'agent_learning_kit-0.3.7-py3-none-any.whl']
    assert len(matches) == 1
    assert hashlib.sha256(matches[0].read_bytes()).hexdigest() == 'cd56fce866e69ec82257037a5c3d1694f197fbf0e27586e243a2137e4ac9e41a'
    return matches[0]


@pytest.fixture
def slim_wheel(tmp_path):
    return make_wheel(tmp_path, 'agent-learning-kit', '0.4.0', {
        'fi/alk/__init__.py': 'SLIM = True\n',
        'fi/alk/optimize.py': 'AVAILABLE = True\n',
        'fi/alk/simulate.py': 'AVAILABLE = True\n',
    })


def isolated_environment(root):
    home = root / 'home'
    home.mkdir()
    temporary = root / 'tmp'
    temporary.mkdir()
    return {
        'PATH': os.defpath, 'HOME': str(home), 'TMPDIR': str(temporary),
        'LANG': 'C.UTF-8', 'PIP_CONFIG_FILE': os.devnull,
        'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PYTHONDONTWRITEBYTECODE': '1',
        'FI_LOGIN_FILE': str(home / 'absent-login.json'),
    }


def run(command, root, environment):
    completed = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout


def new_venv(root, environment):
    destination = root / 'venv'
    run([sys.executable, '-I', '-B', '-m', 'venv', '--without-pip', str(destination)], root, environment)
    return destination / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def install(python, wheel, root, environment, *options):
    run([
        sys.executable, '-I', '-B', '-m', 'pip', '--python', str(python),
        '--disable-pip-version-check', 'install', '--no-index', '--no-cache-dir',
        '--no-compile', '--no-deps', '--only-binary=:all:', *options, str(wheel),
    ], root, environment)


def probe(python, code, root, environment):
    return run([str(python), '-I', '-B', '-c', OFFLINE + code], root, environment)


@pytest.mark.parametrize('namespace', ['fi/opt', 'fi/simulate'])
def test_sdk_source_does_not_own_retired_packages(namespace):
    assert not (PYTHON_ROOT / namespace).exists()


def test_sdk_wheel_boundary(sdk_wheel, slim_wheel):
    paths = record_paths(sdk_wheel)
    assert not paths & record_paths(slim_wheel)
    assert not any(path.startswith(('fi/alk/', 'fi/opt/', 'fi/simulate/')) for path in paths)
    assert {'fi/__init__.py', 'fi/api/__init__.py', 'fi/evals/__init__.py', 'fi/utils/__init__.py'} <= paths
    # This hook lives outside fi because the old distribution overwrites its root.
    assert {'futureagi_namespace_guard.pth', '_futureagi_namespace_guard.py'} <= paths


GUIDANCE = """
import importlib
import fi
assert fi.__version__ == fi.__versions__
assert 'Client' in fi.__all__ and 'FutureAGIClient' in fi.__all__
for old, new in (('fi.opt', 'fi.alk.optimize'), ('fi.simulate', 'fi.alk.simulate')):
    for attempt in range(2):
        try:
            importlib.import_module(old)
        except ImportError as error:
            message = str(error)
            assert old in message and new in message and 'agent-learning-kit' in message, message
            assert 'fi.alk.opt ' not in message
        else:
            raise AssertionError(old + ' must give moved-namespace guidance')
        assert old not in sys.modules
assert 'fi.alk' not in sys.modules
try:
    importlib.import_module('fi.unknown_namespace')
except ModuleNotFoundError as error:
    assert error.name == 'fi.unknown_namespace'
else:
    raise AssertionError('Unknown names must keep normal import semantics')
"""


def test_sdk_only_installed_namespace_guidance(sdk_wheel, tmp_path):
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    install(python, sdk_wheel, tmp_path, environment)
    probe(python, GUIDANCE, tmp_path, environment)


@pytest.mark.parametrize('order', ORDERS)
def test_fat_alk_rejected_before_root_exec_in_both_orders(order, sdk_wheel, fat_wheel, tmp_path):
    assert 'fi/__init__.py' in record_paths(sdk_wheel) & record_paths(fat_wheel)
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    for name in order:
        install(python, {'sdk': sdk_wheel, 'alk': fat_wheel}[name], tmp_path, environment)
    probe(python, """
import importlib
for attempt in range(2):
    try:
        importlib.import_module('fi')
    except ImportError as error:
        assert type(error) is ImportError, repr(error)
        assert str(error) == ('agent-learning-kit 0.3.7 ships its own copy of the fi package, '
                              'which conflicts with futureagi. Upgrade agent-learning-kit to '
                              '0.4.0 or later once it is available, or uninstall it; then reinstall '
                              'futureagi: pip install --force-reinstall --no-deps futureagi'), str(error)
    else:
        raise AssertionError('Fat learning-kit must not silently replace the SDK')
    assert 'fi' not in sys.modules
    assert not any(name.startswith('fi.') for name in sys.modules)
""", tmp_path, environment)


@pytest.mark.parametrize('order', ORDERS)
def test_slim_alk_imports_in_both_orders(order, sdk_wheel, slim_wheel, tmp_path):
    assert not record_paths(sdk_wheel) & record_paths(slim_wheel)
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    for name in order:
        install(python, {'sdk': sdk_wheel, 'alk': slim_wheel}[name], tmp_path, environment)
    probe(python, GUIDANCE + """
from importlib.metadata import distribution
import fi.alk
import fi.alk.optimize
import fi.alk.simulate
assert fi.alk.SLIM and fi.alk.optimize.AVAILABLE and fi.alk.simulate.AVAILABLE
sdk = {str(path) for path in distribution('futureagi').files}
alk = {str(path) for path in distribution('agent-learning-kit').files}
assert not sdk & alk
""", tmp_path, environment)


BROKEN_SDK = (
    "futureagi's files were removed, most likely by upgrading or uninstalling "
    'agent-learning-kit older than 0.4.0; reinstall futureagi: '
    'pip install --force-reinstall --no-deps futureagi'
)


@pytest.mark.parametrize('order', ORDERS)
@pytest.mark.parametrize('remedy', ['upgrade', 'uninstall'])
def test_fat_alk_recovery_requires_sdk_reinstall(order, remedy, sdk_wheel, fat_wheel, slim_wheel, tmp_path):
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    for name in order:
        install(python, {'sdk': sdk_wheel, 'alk': fat_wheel}[name], tmp_path, environment)
    if remedy == 'upgrade':
        install(python, slim_wheel, tmp_path, environment, '--upgrade')
    else:
        run([
            sys.executable, '-I', '-B', '-m', 'pip', '--python', str(python),
            '--disable-pip-version-check', 'uninstall', '--yes', 'agent-learning-kit',
        ], tmp_path, environment)

    # Neither startup nor unrelated imports may inspect distribution metadata.
    probe(python, """
assert 'fi' not in sys.modules
assert 'importlib.metadata' not in sys.modules
import fractions
assert 'importlib.metadata' not in sys.modules
import csv
import importlib
from importlib.metadata import distribution
sdk = distribution('futureagi')
# Distribution.files can filter missing files on newer Python: use raw RECORD.
owned = {row[0] for row in csv.reader(sdk.read_text('RECORD').splitlines()) if row}
assert 'fi/__init__.py' in owned
assert not sdk.locate_file('fi/__init__.py').exists()
for attempt in range(2):
    try:
        importlib.import_module('fi')
    except ImportError as error:
        assert type(error) is ImportError, repr(error)
        assert str(error) == """ + repr(BROKEN_SDK) + """, str(error)
    else:
        raise AssertionError('A removed SDK root must not become a silent namespace')
    assert 'fi' not in sys.modules
    assert not any(name.startswith('fi.') for name in sys.modules)
""", tmp_path, environment)

    install(python, sdk_wheel, tmp_path, environment, '--force-reinstall')
    # Dependencies are borrowed without site/.pth processing, only after fi's
    # search path is fixed to this venv. No SDK module can fall back to the host.
    dependencies = sorted({sysconfig.get_path('purelib'), sysconfig.get_path('platlib')})
    probe(python, """
import csv
from importlib.metadata import distribution
from pathlib import Path
import fi
sdk = distribution('futureagi')
root = sdk.locate_file('fi').resolve()
assert root.is_relative_to(Path(sys.prefix).resolve())
assert fi.__file__ and Path(fi.__file__).resolve() == root / '__init__.py'
assert [Path(path).resolve() for path in fi.__path__] == [root]
owned = {row[0] for row in csv.reader(sdk.read_text('RECORD').splitlines()) if row}
assert {'fi/__init__.py', 'fi/api/__init__.py', 'fi/evals/__init__.py', 'fi/utils/__init__.py'} <= owned
missing = sorted(path for path in owned if path.startswith('fi/') and not sdk.locate_file(path).is_file())
assert not missing, missing
sys.path.extend(""" + repr(dependencies) + """)
from fi import Client
assert Client.__module__ == 'fi.platform._client'
assert Path(sys.modules[Client.__module__].__file__).resolve().is_relative_to(root)
assert [Path(path).resolve() for path in fi.__path__] == [root]
""", tmp_path, environment)
    if remedy == 'uninstall':
        probe(python, """
from importlib.metadata import PackageNotFoundError, distribution
try:
    distribution('agent-learning-kit')
except PackageNotFoundError:
    pass
else:
    raise AssertionError('Uninstall must leave no kit distribution')
""", tmp_path, environment)
        # Optional slim installation after repair must remain possible.
        install(python, slim_wheel, tmp_path, environment)
    probe(python, """
from pathlib import Path
import fi
import fi.alk
import fi.alk.optimize
import fi.alk.simulate
assert fi.alk.SLIM and fi.alk.optimize.AVAILABLE and fi.alk.simulate.AVAILABLE
assert Path(fi.alk.__file__).resolve().is_relative_to(Path(fi.__file__).resolve().parent)
""", tmp_path, environment)


@pytest.mark.parametrize('order', ORDERS)
def test_real_legacy_provider_is_not_shadowed(order, sdk_wheel, tmp_path):
    provider = make_wheel(tmp_path, 'legacy-namespace-provider', '1.0', {
        'fi/opt/__init__.py': 'PROVIDER = True\n',
        'fi/simulate/__init__.py': 'PROVIDER = True\n',
    })
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    for name in order:
        install(python, {'sdk': sdk_wheel, 'alk': provider}[name], tmp_path, environment)
    probe(python, """
import fi.opt
import fi.simulate
assert fi.opt.PROVIDER and fi.simulate.PROVIDER
""", tmp_path, environment)


def test_late_meta_path_provider_and_its_import_errors_take_precedence(sdk_wheel, tmp_path):
    environment = isolated_environment(tmp_path)
    python = new_venv(tmp_path, environment)
    install(python, sdk_wheel, tmp_path, environment)
    probe(python, """
import fi
import importlib
import importlib.util
class Provider:
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ('fi.opt', 'fi.simulate'):
            return importlib.util.spec_from_loader(fullname, self)
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        if module.__name__ == 'fi.simulate':
            raise ImportError('provider dependency missing')
        module.PROVIDER = True
sys.meta_path.append(Provider())
import fi.opt
assert fi.opt.PROVIDER
try:
    import fi.simulate
except ImportError as error:
    assert str(error) == 'provider dependency missing'
else:
    raise AssertionError('Provider error must not be swallowed')
""", tmp_path, environment)


@pytest.mark.parametrize('version,files,reject', [
    ('0.3.7', [], True),
    ('0.3.7', None, True),
    ('0.4.0rc1', [], True),
    ('0.4.0.dev1', [], True),
    ('0.4.0', [], False),
    ('0.4', [], False),
    ('0.4.0.post1.dev1', [], False),
    ('1!0.3.7', [], False),
    ('0.4.0', ['fi/evals/__init__.py'], True),
    ('1.0.0', ['fi/evals/types.py'], True),
    ('0.4.0', ['fi/alk/evals/__init__.py'], False),
])
def test_overlap_detection_from_metadata_without_importing_alk(version, files, reject, tmp_path):
    environment = isolated_environment(tmp_path)
    code = """
import importlib.metadata
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
version, files, reject = __import__('json').loads(sys.argv[2])
with patch('importlib.metadata.distribution', return_value=SimpleNamespace(version=version, files=files)):
    try:
        import fi
    except ImportError as error:
        assert reject, str(error)
        assert str(error) == ('agent-learning-kit ' + version + ' ships its own copy of the fi package, '
                              'which conflicts with futureagi. Upgrade agent-learning-kit to '
                              '0.4.0 or later once it is available, or uninstall it; then reinstall '
                              'futureagi: pip install --force-reinstall --no-deps futureagi')
    else:
        assert not reject, 'Expected fat-layout rejection'
assert 'fi.alk' not in sys.modules
"""
    import json
    run([sys.executable, '-I', '-B', '-c', OFFLINE + code, str(PYTHON_ROOT), json.dumps([version, files, reject])], tmp_path, environment)


@pytest.mark.parametrize('sdk_installed,root_present,record,reject', [
    (False, False, None, False),
    (True, True, 'fi/__init__.py,,\n', False),
    (True, False, 'fi/__init__.py,,\n', True),
    (True, False, 'fi/__init__.py,,\nfi/api/__init__.py,,\n', True),
    (True, False, None, False),
    (True, False, 'editable.pth,,\n', False),
])
def test_sdk_root_guard_uses_raw_record_only_when_needed(sdk_installed, root_present, record, reject, tmp_path):
    environment = isolated_environment(tmp_path)
    site = tmp_path / 'site'
    site.mkdir()
    if root_present:
        (site / 'fi').mkdir()
        (site / 'fi/__init__.py').write_text('')
    code = """
import importlib.metadata as metadata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, sys.argv[1])
import _futureagi_namespace_guard as guard
sdk_installed, record, reject, message = __import__('json').loads(sys.argv[3])
sdk = SimpleNamespace(locate_file=lambda path: Path(sys.argv[2]) / path,
                      read_text=Mock(return_value=record))
def distribution(name):
    if name == 'futureagi' and sdk_installed:
        return sdk
    raise metadata.PackageNotFoundError(name)
with patch('importlib.metadata.distribution', side_effect=distribution) as lookup:
    guard.install()
    guard.install()
    finders = [finder for finder in sys.meta_path if isinstance(finder, guard._RootGuard)]
    assert len(finders) == 1
    finder = finders[0]
    assert finder.find_spec('fractions') is None
    assert finder.find_spec('fi_other') is None
    lookup.assert_not_called()
    try:
        assert finder.find_spec('fi') is None
    except ImportError as error:
        assert reject, str(error)
        assert type(error) is ImportError and str(error) == message
    else:
        assert not reject, 'Missing SDK root must be rejected'
assert sdk.read_text.call_count <= 1
if sdk.read_text.call_count:
    sdk.read_text.assert_called_once_with('RECORD')
assert 'fi' not in sys.modules
"""
    run([
        sys.executable, '-I', '-B', '-c', OFFLINE + code, str(PYTHON_ROOT), str(site),
        json.dumps([sdk_installed, record, reject, BROKEN_SDK]),
    ], tmp_path, environment)


def test_pth_only_registers_without_metadata_or_fi_imports(tmp_path):
    environment = isolated_environment(tmp_path)
    code = """
import builtins
from pathlib import Path
sys.path.insert(0, sys.argv[1])
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    assert name != 'fi' and not name.startswith('fi.'), name
    assert name != 'importlib.metadata', name
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
try:
    hook = (Path(sys.argv[1]) / 'futureagi_namespace_guard.pth').read_text()
    exec(hook)
    exec(hook)
finally:
    builtins.__import__ = original_import
import _futureagi_namespace_guard as guard
assert sum(isinstance(finder, guard._RootGuard) for finder in sys.meta_path) == 1
assert 'fi' not in sys.modules
assert 'importlib.metadata' not in sys.modules
"""
    run([sys.executable, '-I', '-B', '-c', OFFLINE + code, str(PYTHON_ROOT)], tmp_path, environment)


def test_source_reload_registers_only_one_fallback(tmp_path):
    environment = isolated_environment(tmp_path)
    code = """
import importlib
sys.path.insert(0, sys.argv[1])
import fi
before = tuple(sys.meta_path)
importlib.reload(fi)
importlib.reload(fi)
assert tuple(sys.meta_path) == before
"""
    run([sys.executable, '-I', '-B', '-c', OFFLINE + code + GUIDANCE, str(PYTHON_ROOT)], tmp_path, environment)
