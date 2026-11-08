"""Offline installed-package checks; run only in a prepared disposable runner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

root, evidence = map(lambda p: Path(p).resolve(), sys.argv[1:3])
python = root / '.sdk-python/bin/python'
tools = root / '.proof-tools/node_modules/.bin'
os.environ['PATH'] = str(tools) + os.pathsep + os.environ['PATH']
os.environ.update(npm_config_offline='true', npm_config_ignore_scripts='true',
                  PIP_NO_INDEX='1', UV_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
mode = sys.argv[3]


def run(argv, cwd):
    subprocess.run(list(map(str, argv)), cwd=cwd, check=True)


if mode == 'python':
    wheels = evidence / 'wheels'
    wheels.mkdir()
    run([python, '-I', '-B', '-m', 'build', '--wheel', '--no-isolation', '--outdir', wheels], root / 'python')
    wheel, = wheels.glob('*.whl')
    consumer = evidence / 'wheel-consumer'
    run(['uv', 'venv', '--python', python, consumer], evidence)
    installed_python = consumer / 'bin/python'
    run(['uv', 'pip', 'install', '--python', installed_python, '--offline', wheel, 'mypy'], evidence)
    for name in ('consumer.py', 'docs_examples.py'):
        shutil.copyfile(root / 'python/consumer' / name, consumer / name)
    shutil.copytree(root / 'docs/sdk-reference', consumer / 'sdk-reference')
    run([installed_python, '-I', '-B', '-c',
         'import fi,pathlib,sys; p=pathlib.Path(fi.__file__).resolve(); assert p.is_relative_to(pathlib.Path(sys.prefix).resolve()),p'], consumer)
    run([installed_python, '-I', '-B', 'consumer.py'], consumer)
    run([installed_python, '-I', '-B', '-m', 'mypy', '--strict', '--follow-imports=silent', 'consumer.py'], consumer)
    run([installed_python, '-I', '-B', 'docs_examples.py', 'sdk-reference'], consumer)
elif mode == 'typescript':
    package = root / 'typescript/futureagi'
    packed = evidence / 'candidate'
    run(['node', package / 'gateway-client/scripts/stage-package.cjs', packed], root)
    tarball, = packed.glob('*.tgz')
    with tarfile.open(tarball) as archive:
        manifest = json.load(archive.extractfile('package/package.json'))
        assert 'scripts' not in manifest and 'devDependencies' not in manifest
        (evidence / 'candidate-files.json').write_text(json.dumps(sorted(archive.getnames()), indent=2) + '\n')
    consumer = evidence / 'tarball-consumer'
    consumer.mkdir()
    (consumer / 'package.json').write_text('{"private":true,"type":"module"}\n')
    run(['npm', 'install', '--offline', '--ignore-scripts', '--no-audit', '--no-fund', tarball, 'typescript@5.6.3'], consumer)
    for path in (package / 'consumer').glob('*.mts'):
        shutil.copyfile(path, consumer / path.name)
    shutil.copyfile(package / 'consumer/tsconfig.json', consumer / 'tsconfig.json')
    run(['node', package / 'scripts/docs-examples.mjs', root / 'docs/sdk-reference', consumer / 'docs-examples.mts'], consumer)
    run(['node', consumer / 'node_modules/typescript/bin/tsc', '-p', 'tsconfig.json'], consumer)
    # Preserve the shipped consumer's ESM, loopback HTTP error, and CJS assertions.
    source = (package / 'scripts/check-consumer.sh').read_text()
    marker = 'echo "consumer: ESM import"'
    assert source.count(marker) == 1
    runtime = consumer / 'runtime.sh'
    runtime.write_text('set -eu\n' + marker + source.split(marker, 1)[1])
    run(['bash', runtime], consumer)
else:
    raise SystemExit('unknown package proof mode')
