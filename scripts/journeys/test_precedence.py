"""Run the real credential assertion against deliberately incorrect resolvers."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_python import check_config
from probe_common import Checks
from test_matrix import policy


def outcome(ignored):
    class Client:
        def __init__(self, **options):
            self.api = os.environ['FI_API_KEY'] if 'api' in ignored else options.get('api_key', os.environ['FI_API_KEY'])
            self.secret = os.environ['FI_SECRET_KEY'] if 'secret' in ignored else options.get('secret_key', os.environ['FI_SECRET_KEY'])
            self.url = options.get('base_url', os.environ['FI_BASE_URL'])
            self.users = SimpleNamespace(current=self.current)

        def current(self):
            request = Request(self.url + '/accounts/user-info/', headers={'X-Api-Key': self.api, 'X-Secret-Key': self.secret})
            try:
                with urlopen(request, timeout=5):
                    pass
            except HTTPError:
                pass  # Isolate header assertions from the fixture's status handling.

        def close(self):
            pass

    class OnlyPrecedence(Checks):
        def run(self, name, action):
            if name == 'config.argument-precedence':
                super().run(name, action)

    checks = OnlyPrecedence()
    with patch.dict(sys.modules, {'fi': SimpleNamespace(FutureAGIClient=Client)}), patch.dict(os.environ):
        check_config(checks, policy())
    return next(c['state'] for c in checks.rows if c['name'] == 'config.argument-precedence')


class PrecedenceTests(unittest.TestCase):
    def test_correct_resolver_passes(self):
        self.assertEqual(outcome(set()), 'PASS')

    def test_environment_snapshot_resolvers_fail(self):
        for ignored in ({'api'}, {'secret'}, {'api', 'secret'}):
            with self.subTest(ignored=ignored):
                self.assertEqual(outcome(ignored), 'FAIL')


if __name__ == '__main__':
    unittest.main()
