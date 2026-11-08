"""Archive-only residue must fail even with complete, passing runtime absence."""
import copy
import json
from pathlib import Path
import sys
import tarfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from absence_evidence import required, runtimes
from artifacts import absence_checks
from matrix import build
from test_matrix import policy
from catalog import SURFACES


def check_residue(namespace, files, expected=None):
    p = policy()
    p['docs_complete'] = True
    # Every other surface is ON, so nested ownership does not mask this result.
    for name in p['states']:
        p['states'][name] = {'py': 'ON', 'ts': 'OFF' if name == namespace else 'ON'}
    inventory = {'py': [], 'ts': files, 'package': {'exports': {'.': './root.js'}}, 'docs': ''}
    archives = {'py': [], 'ts': absence_checks(inventory, p, 'ts', expected)}
    probes = {runtime: {'checks': [{'name': name, 'state': 'PASS'} for name in
              required(namespace, p['surfaces'][namespace], 'ts') + ['install.esm.probe', 'install.cjs.probe']]}
              for runtime in runtimes('ts')}
    rows = build({'served': ['sdk-artifacts'], 'admitted': ['sdk']}, p, probes, archives,
                 ['N00'], {'denied_count': 0})
    archive = next(c for c in archives['ts'] if c['name'] == 'absence.' + namespace + '.archive')
    cell = next(c for c in rows if c['namespace'] == namespace and c['variant'] == 'absence')
    return archive, cell


class EmittedAbsenceTests(unittest.TestCase):
    def test_every_namespace_retained_output_and_declaration(self):
        from ts_inventory import snapshot
        expected = snapshot(TARBALL)
        with tarfile.open(TARBALL) as archive:
            names = [m.name for m in archive.getmembers() if m.isfile()]
        for row in expected['namespaces']:
            namespace = row['namespace']
            if namespace not in SURFACES:
                continue  # Core install/config cannot be removed independently.
            files = row['files']
            if not files:
                # Unemitted namespaces still need fallibility, not a vacuous pass.
                # Use the public nested accessor identity with the real compiler layouts.
                modules, accessors, _, _ = SURFACES[namespace]
                identity = next((a for a in accessors if '.' in a), modules[0]).replace('.', '/')
                files = [n.replace('/knowledge-bases/', '/' + identity + '/') for n in names
                         if '/knowledge-bases/' in n]
            self.assertTrue(files, namespace)
            for file in files:
                with self.subTest(namespace=namespace, file=file):
                    archive, cell = check_residue(namespace, [file], expected)
                    self.assertEqual(archive['state'], 'FAIL')
                    self.assertEqual(cell['state'], 'FAIL')

    def test_nested_helpers_do_not_claim_unrelated_namespaces(self):
        from ts_inventory import owners
        self.assertEqual(owners('package/dist/esm/gateway/models/index.d.ts.map'), ['gateway'])
        self.assertEqual(owners('package/dist/src/gateway-management/keys.js'), ['gateway_management'])
        self.assertEqual(owners('package/dist/src/agents/runs/index.js'), ['agents', 'runs'])
        self.assertEqual(owners('package/dist/esnext/knowledge-bases/index.d.ts'), ['knowledge_bases'])

    def test_checked_inventory_matches_and_fails_on_drift(self):
        from ts_inventory import EXPECTED, compare, snapshot
        expected = json.loads((EXPECTED_OVERRIDE or EXPECTED).read_text())
        actual = snapshot(TARBALL)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual['namespaces']), 20)
        names = [f for row in actual['namespaces'] for f in row['files']]
        p = policy()
        self.assertEqual(compare(names, p, expected)['state'], 'PASS')
        self.assertEqual(compare(names + ['package/dist/new-format/opaque.js'], p, expected)['state'], 'FAIL')
        # Removal is permitted only for OFF surfaces; an ON surface disappearing is drift.
        kb = next(r['files'] for r in actual['namespaces'] if r['namespace'] == 'knowledge_bases')
        without = [n for n in names if n not in kb]
        self.assertEqual(compare(without, p, expected)['state'], 'PASS')
        p['states']['knowledge_bases']['ts'] = 'ON'
        self.assertEqual(compare(without, p, expected)['state'], 'FAIL')
        mutated = copy.deepcopy(expected)
        row = next(r for r in mutated['namespaces'] if r['namespace'] == 'knowledge_bases')
        row['files'].remove(kb[0])
        self.assertEqual(compare(names, p, mutated)['state'], 'FAIL')

    def test_real_knowledge_base_artifact_residue(self):
        with tarfile.open(TARBALL) as archive:
            names = [m.name for m in archive.getmembers() if m.isfile() and '/knowledge-bases/' in m.name]
        self.assertTrue(names)
        # Each runtime/declaration/map must fail independently, not only alongside JS.
        for name in names:
            with self.subTest(file=name):
                archive, cell = check_residue('knowledge_bases', [name])
                self.assertEqual(archive['state'], 'FAIL')
                self.assertEqual(cell['state'], 'FAIL')

    def test_nested_run_artifact_residue(self):
        with tarfile.open(TARBALL) as archive:
            # Derive compiler output layouts and suffixes from the real tarball.
            files = [m.name.replace('/knowledge-bases/', '/agents/runs/') for m in archive.getmembers()
                     if m.isfile() and '/knowledge-bases/' in m.name]
        self.assertTrue(files)
        for file in files:
            with self.subTest(file=file):
                archive, cell = check_residue('runs', [file])
                self.assertEqual(archive['state'], 'FAIL')
                self.assertEqual(cell['state'], 'FAIL')


if __name__ == '__main__':
    TARBALL = Path(sys.argv.pop(1))
    EXPECTED_OVERRIDE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else None
    unittest.main()
