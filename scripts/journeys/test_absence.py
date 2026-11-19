"""Required absence evidence, including every supported consumer profile and mode."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifacts import absence_checks
from matrix import build
from test_matrix import policy


def fixture():
    p = policy()
    p['docs_complete'] = True
    archive = {lang: absence_checks({'py': [], 'ts': [], 'package': {}, 'docs': ''}, p, lang)
               for lang in ('py', 'ts')}
    prefix = 'absence.datasets.'
    py = ['import.fi.datasets', 'accessor.FutureAGIClient.datasets',
          'accessor.AsyncFutureAGIClient.datasets', 'root.datasets', 'cli']
    ts = [mode + '.' + name for mode in ('esm', 'cjs')
          for name in ('subpath.datasets', 'accessor.datasets')]
    probes = {}
    for v in ('3.10', '3.12'):
        for extra in ('base', 'evals', 'tracing'):
            probes[f'py-{v}-{extra}'] = {'checks': [{'name': prefix + n, 'state': 'PASS'} for n in py]
                                       + [{'name': 'install.probe', 'state': 'PASS'}]}
    for v in ('20', '22'):
        probes['ts-' + v] = {'checks': [{'name': prefix + n, 'state': 'PASS'} for n in ts]
                            + [{'name': 'install.esm.probe', 'state': 'PASS'}, {'name': 'install.cjs.probe', 'state': 'PASS'}]}
    return p, probes, archive


def result(p, probes, archive):
    rows = build({'served': ['sdk-artifacts'], 'admitted': ['sdk']}, p, probes, archive, ['N00'], {'denied_count': 0})
    return next(r for r in rows if r['id'] == 'N02' and r['variant'] == 'absence')['state']


class AbsenceTests(unittest.TestCase):
    def test_complete_evidence_passes(self):
        self.assertEqual(result(*fixture()), 'PASS')

    def test_each_missing_runtime_is_unevaluated(self):
        p, probes, archive = fixture()
        for runtime in probes:
            with self.subTest(runtime=runtime):
                missing = copy.deepcopy(probes)
                del missing[runtime]
                self.assertEqual(result(p, missing, archive), 'NOT-EVALUATED')

    def test_each_missing_required_check_is_unevaluated(self):
        p, probes, archive = fixture()
        for runtime, probe in probes.items():
            for check in probe['checks']:
                with self.subTest(runtime=runtime, check=check['name']):
                    missing = copy.deepcopy(probes)
                    missing[runtime]['checks'].remove(check)
                    self.assertEqual(result(p, missing, archive), 'NOT-EVALUATED')

    def test_missing_archive_or_docs_is_unevaluated(self):
        p, probes, archive = fixture()
        for lang in archive:
            for check in [c for c in archive[lang] if c['name'].startswith('absence.datasets.')]:
                with self.subTest(lang=lang, check=check['name']):
                    missing = copy.deepcopy(archive)
                    missing[lang].remove(check)
                    self.assertEqual(result(p, probes, missing), 'NOT-EVALUATED')

    def test_on_language_does_not_require_absence(self):
        p, probes, archive = fixture()
        p['states']['datasets']['py'] = 'ON'
        self.assertEqual(result(p, {k: v for k, v in probes.items() if k.startswith('ts-')}, archive), 'PASS')


if __name__ == '__main__':
    unittest.main()
