"""The recorder guards checkouts directly beneath the filesystem root too."""

from pathlib import Path

from . import _hygiene, test_parity_hygiene


def test_single_component_checkout_is_guarded(tmp_path, monkeypatch):
    checkout = Path("/" + "checkout")
    monkeypatch.setattr(_hygiene, "REPO", checkout)
    monkeypatch.setattr(test_parity_hygiene, "REPO", checkout)
    test_parity_hygiene.test_write_checked_refuses_a_leak_and_writes_nothing(
        tmp_path / "write"
    )
    test_parity_hygiene.test_the_recorder_refuses_a_case_that_records_its_checkout(
        tmp_path / "record", monkeypatch
    )
