"""Cloud-only, real-container controls for whole-process-tree network accounting."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from consumer import Consumers
from matrix import build
from test_matrix import policy

ROOT = Path(sys.argv.pop(1)).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
KIT = Path(__file__).resolve().parent


class NetworkTreeTests(unittest.TestCase):
    def test_caught_errors_cannot_leave_a_green_matrix(self):
        for language, modes in [('py', ['sendmsg4', 'sendmsg6', 'child-tcp', 'grandchild-udp']),
                                ('ts', ['resolver', 'child-tcp', 'child-udp'])]:
            for mode in modes:
                with self.subTest(language=language, mode=mode):
                    out = ROOT / (language + '-' + mode)
                    out.mkdir()
                    artifact = out / 'unused.json'
                    artifact.write_text('{}')
                    with Consumers(KIT, out) as consumers:
                        tag = 'python:3.12-slim-bookworm' if language == 'py' else 'node:22-bookworm-slim'
                        result_dir = out / 'result'
                        with consumers.container(tag, artifact, artifact, result_dir, False) as (box, _):
                            consumers.offline(box)
                            argv = ['python', '-I', '/kit/network_control.py', mode] if language == 'py' else ['node', '/kit/network_control_node.cjs', mode]
                            consumers.execute(box, 'negative-control', argv)
                        probe = json.loads((result_dir / 'probe.json').read_text())
                        observed = getattr(consumers, 'observations', {})
                        denials = probe['network']['denied_count'] + sum(x['denied_count'] for x in observed.values())
                        (out / 'evidence.json').write_text(json.dumps({'process': probe['network'], 'container': observed, 'denied_count': denials}, indent=2))
                    self.assertTrue(observed and all(x['complete'] for x in observed.values()))
                    self.assertGreater(denials, 0, 'Caught OS errors must still count as attempted egress')
                    for trace in out.glob('*.trace'):
                        self.assertNotIn('not-a-credential-payload', trace.read_text())
                    rows = build({'served': ['sdk-artifacts'], 'admitted': ['sdk']}, policy(),
                                 {'py-3.12-base' if language == 'py' else 'ts-22': probe}, {'py': [], 'ts': []}, ['N00'], {'denied_count': denials})
                    row = next(r for r in rows if r['id'] == 'N00' and r['variant'] == language)
                    self.assertEqual(row['state'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
