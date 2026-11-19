"""Exercise the installed wheel, with and without its console-script declaration."""
import base64
import configparser
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from consumer import Consumers
from run import effective_policy


REQUIRED = ('install.doctor-status', 'install.doctor-json', 'config.login-from-env')


def mutate_entrypoint(source, destination, broken=False):
    with zipfile.ZipFile(source) as wheel:
        content = {i.filename: wheel.read(i) for i in wheel.infolist()}
    entry = next(n for n in content if n.endswith('.dist-info/entry_points.txt'))
    cfg = configparser.ConfigParser()
    cfg.read_string(content[entry].decode())
    assert cfg.has_option('console_scripts', 'futureagi-py')
    if broken:
        cfg.set('console_scripts', 'futureagi-py', 'fi._cli.main:missing_entrypoint')
    else:
        cfg.remove_option('console_scripts', 'futureagi-py')
    stream = io.StringIO()
    cfg.write(stream)
    content[entry] = stream.getvalue().encode()
    record = next(n for n in content if n.endswith('.dist-info/RECORD'))
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    for name, data in content.items():
        if name != record:
            checksum = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            writer.writerow([name, 'sha256=' + checksum, len(data)])
    writer.writerow([record, '', ''])
    content[record] = stream.getvalue().encode()
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as wheel:
        for name, data in content.items():
            wheel.writestr(name, data)
    # Only packaging metadata changed; every installed Python byte is retained.
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination) as mutant:
        assert all(original.read(n) == mutant.read(n) for n in original.namelist() if n not in (entry, record))


class CheckedConsumers(Consumers):
    expect_cli = True

    def execute(self, box, name, argv, required=True, cwd='/'):
        if name == 'python-probe':
            assertion = 'is not None' if self.expect_cli else 'is None'
            super().execute(box, 'console-entrypoint-presence', ['python', '-I', '-c',
                            "import shutil; assert shutil.which('futureagi-py') " + assertion])
        return super().execute(box, name, argv, required, cwd)


def main(wheel, out):
    out.mkdir(parents=True)
    kit = Path(__file__).resolve().parent
    p = out / 'policy.json'
    p.write_text(json.dumps(effective_policy(json.loads((kit / 'historical-policy.json').read_text()))))
    mutant_dir = out / 'mutant-input'
    mutant_dir.mkdir()
    mutant = mutant_dir / wheel.name
    mutate_entrypoint(wheel, mutant)
    broken_dir = out / 'broken-input'
    broken_dir.mkdir()
    broken = broken_dir / wheel.name
    mutate_entrypoint(wheel, broken, broken=True)
    evidence = {}
    for label, artifact, expected in [('original', wheel, 'PASS'), ('missing-entrypoint', mutant, 'FAIL'),
                                      ('broken-entrypoint', broken, 'FAIL')]:
        destination = out / label
        destination.mkdir()
        consumers = CheckedConsumers(kit, destination)
        consumers.expect_cli = label != 'missing-entrypoint'
        with consumers:
            _, result = consumers.python('3.12', 'base', artifact.resolve(), p.resolve(), True)
        checks = {c['name']: c['state'] for c in result['checks']}
        evidence[label] = {'checks': checks, 'network': consumers.observations,
                           'expected': expected, 'pass': all(checks.get(n) == expected for n in REQUIRED)}
        assert consumers.observations and all(o['complete'] and o['denied_count'] == 0 for o in consumers.observations.values())
    (out / 'cli-controls.json').write_text(json.dumps(evidence, indent=2) + '\n')
    assert all(e['pass'] for e in evidence.values()), evidence


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
