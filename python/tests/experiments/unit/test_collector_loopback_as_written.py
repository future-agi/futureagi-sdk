"""The experiments run's collector endpoint judges loopback on the host as it is written.

An ``http://`` collector is accepted for loopback, and for the host of an ``http://`` API base. ``localhost.``, a
spelling of an address other than the dotted form (``127.1``, ``0x7f.0.0.1``) and a name that only folds to
``localhost`` (``ⅼocalhost``) are not loopback.
"""

import pytest

from fi.experiments._tracing.export import _validate_collector_endpoint
from fi.experiments.errors import ExperimentError

BASE = "https://api.example.test"


def accepted(host):
    endpoint = f"http://{host}:4318/v1/traces"
    try:
        return _validate_collector_endpoint(endpoint, base_url=BASE) == endpoint
    except ExperimentError:
        return False


@pytest.mark.parametrize("host", ["localhost", "LOCALHOST", "127.0.0.1", "127.9.9.9", "[::1]"])
def test_loopback_as_written_is_accepted(host):
    assert accepted(host)


@pytest.mark.parametrize("host", ["ⅼocalhost", "localhost.", "127.1", "0x7f.0.0.1", "2130706433", "0177.0.0.1",
                                  "127.0.0.1.", "app.localhost"])
def test_other_spellings_are_not_loopback(host):
    assert not accepted(host)
