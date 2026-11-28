"""The 0.9.0 changelog says how a Future AGI gRPC or HTTP exporter picks TLS, in the same plain wording."""

import re

import pytest

from tests.experiments.unit.test_changelog_traces_wording import (
    BANNED,
    HEADING,
    section,
)

NEEDED = [
    "OTEL_EXPORTER_OTLP_TRACES_INSECURE",
    "OTEL_EXPORTER_OTLP_INSECURE",
    "INSECURE_HTTP_REFUSED",
    "connects with TLS",
    "correct the path or unset",
    "FI_COLLECTOR_ENDPOINT",
]


@pytest.mark.parametrize("needed", NEEDED)
def test_the_notes_name_what_a_user_needs(needed):
    assert needed in section(HEADING)


def test_the_insecure_variables_are_named_together():
    notes = section(HEADING)
    assert re.search(r"OTEL_EXPORTER_OTLP_INSECURE`?\s+and\s+`?OTEL_EXPORTER_OTLP_TRACES_INSECURE", notes)


def test_the_notes_give_the_action_for_an_unreadable_tls_file():
    notes = " ".join(section(HEADING).split())
    assert "unreadable_tls_file" in notes and "correct the path or unset the named setting" in notes


def test_a_blank_collector_endpoint_is_described_both_ways():
    notes = " ".join(section(HEADING).split())
    assert '`FI_COLLECTOR_ENDPOINT` of `""` counts as unset' in notes
    assert "only white space is refused" in notes


@pytest.mark.parametrize("pattern", BANNED)
def test_the_new_notes_hold_no_banned_word(pattern):
    assert re.findall(pattern, section(HEADING), flags=re.IGNORECASE) == []
