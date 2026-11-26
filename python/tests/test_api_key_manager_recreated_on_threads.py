"""``APIKeyManager`` created again on one thread while another thread reads the same manager.

The manager reads ``FI_API_KEY`` and ``FI_SECRET_KEY`` each time it is created. While one thread creates it again
and again, another thread reads its ``headers`` and the headers it sends; each read returns the keys from the
environment.
"""

from __future__ import annotations

import secrets
import sys
import threading

from fi.api.auth import APIKeyManager
from fi.utils.errors import MissingAuthError

CREATIONS = 1500


def test_reads_during_repeated_creation_return_the_keys_from_the_environment(monkeypatch):
    key = "fikey-e-" + secrets.token_hex(10)
    secret = "fisec-e-" + secrets.token_hex(10)
    monkeypatch.setenv("FI_API_KEY", key)
    monkeypatch.setenv("FI_SECRET_KEY", secret)
    monkeypatch.setattr(APIKeyManager, "_instance", None)
    expected = {"X-Api-Key": key, "X-Secret-Key": secret}
    manager = APIKeyManager()
    stop = threading.Event()
    counts = {"reads": 0, "refused": 0, "other_headers": 0, "other_sent_headers": 0}

    def create() -> None:
        try:
            for _ in range(CREATIONS):
                APIKeyManager().close()
        finally:
            stop.set()

    def read() -> None:
        while not stop.is_set():
            counts["reads"] += 1
            try:
                if manager.headers != expected:
                    counts["other_headers"] += 1
            except MissingAuthError:
                counts["refused"] += 1
            if manager._default_headers != expected:
                counts["other_sent_headers"] += 1

    interval = sys.getswitchinterval()
    try:
        sys.setswitchinterval(1e-6)
        threads = [threading.Thread(target=read), threading.Thread(target=create)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        sys.setswitchinterval(interval)
        manager.close()
    assert counts["reads"] > 0, counts
    assert (counts["refused"], counts["other_headers"], counts["other_sent_headers"]) == (0, 0, 0), counts
