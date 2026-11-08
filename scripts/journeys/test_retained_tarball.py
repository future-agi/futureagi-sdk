"""Installed hidden-surface control: runtime removal cannot hide compiled bytes."""
import copy
import io
import json
from pathlib import Path
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifacts import absence_checks
from catalog import SURFACES
from consumer import Consumers
from matrix import build
from test_matrix import policy
from ts_inventory import snapshot


def mutate(source, target):
    with tarfile.open(source) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    original = dict(files)
    rows = snapshot(source)['namespaces']
    provenance = {}
    # Historical packages need not contain every planned namespace. Use emitted
    # compiler-layout fixtures for those holes, and label them as synthetic.
    for row in rows:
        name = row['namespace']
        if name not in SURFACES:
            continue
        provenance[name] = {'kind': 'retained-artifact', 'files': row['files']}
        if not row['files']:
            modules, accessors, _, _ = SURFACES[name]
            identity = next((a for a in accessors if '.' in a), modules[0]).replace('.', '/')
            added = {}
            for path, data in original.items():
                if '/knowledge-bases/index.' in path:
                    added[path.replace('/knowledge-bases/', '/' + identity + '/')] = data
            assert added, name
            files.update(added)
            provenance[name] = {'kind': 'synthetic-layout', 'files': sorted(added)}
    pkg = json.loads(files['package/package.json'])
    root = pkg['exports']['.']
    # Strip every public namespace accessor/root export/subpath, not its files.
    esm = b'export class FutureAGIClient {}\n'
    cjs = b'exports.FutureAGIClient = class FutureAGIClient {};\n'
    files['package/' + root['import'].removeprefix('./')] = esm
    files['package/' + root['require'].removeprefix('./')] = cjs
    files['package/' + root['types'].removeprefix('./')] = b'export declare class FutureAGIClient {}\n'
    pkg['exports'] = {'.': root}
    for key in ('dependencies', 'optionalDependencies', 'peerDependencies', 'bin', 'scripts'):
        pkg.pop(key, None)
    files['package/package.json'] = json.dumps(pkg).encode()
    # The known documentation corpus is empty in this negative fixture.
    files = {n: data for n, data in files.items() if not n.lower().endswith(('.md', '.mdx'))}
    for item in provenance.values():
        if item['kind'] == 'retained-artifact':
            assert all(files[n] == original[n] for n in item['files'])
    with tarfile.open(target, 'w:gz') as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o644
            archive.addfile(member, io.BytesIO(data))
    return files, pkg, provenance


def main(tarball, out):
    out.mkdir(parents=True)
    p = policy()
    p['docs_complete'] = True
    # Only TypeScript is under test; this does not qualify Python absence.
    for row in p['states'].values():
        row['py'] = 'ON'
    path = out / 'policy.json'
    path.write_text(json.dumps(p))
    mutant_dir = out / 'mutant-input'
    mutant_dir.mkdir()
    mutant = mutant_dir / tarball.name
    files, package, provenance = mutate(tarball, mutant)
    probes = {}
    consumers = Consumers(Path(__file__).resolve().parent, out)
    with consumers:
        for version in ('20', '22'):
            label, result = consumers.node(version, mutant, path, False)
            probes[label] = result
    (out / 'probes.json').write_text(json.dumps(probes, indent=2))
    assert all(c['state'] == 'PASS' for p in probes.values() for c in p['checks']), probes
    assert consumers.observations and all(o['complete'] and o['denied_count'] == 0 for o in consumers.observations.values())
    declarations = {n: data.decode('utf8') for n, data in files.items() if n.endswith('.d.ts')}
    archive = {'py': [], 'ts': absence_checks({'ts': list(files), 'py': [], 'package': package,
                                             'docs': '', 'ts_declarations': declarations}, p, 'ts')}
    rows = build({'served': ['sdk-artifacts'], 'admitted': ['sdk']}, p, probes, archive, ['N00'],
                 {'denied_count': 0, 'complete': True})
    evidence = []
    for namespace, source in provenance.items():
        cell = next(r for r in rows if r['namespace'] == namespace and r['variant'] == 'absence')
        file_check = next(c for c in cell['checks'] if c['name'] == 'absence.' + namespace + '.archive')
        evidence.append({'namespace': namespace, **source, 'archive': file_check['state'], 'cell': cell['state']})
    (out / 'retained-controls.json').write_text(json.dumps(evidence, indent=2) + '\n')
    assert len(evidence) == 18 and all(e['archive'] == e['cell'] == 'FAIL' for e in evidence), evidence


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
