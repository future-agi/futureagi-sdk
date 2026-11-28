"""The 0.8.0 changelog names each error code once, with the action it asks for, and names no other code for a situation."""

import pytest

from tests.experiments.unit.test_changelog_traces_wording import release_section

NAMED_ONCE = [
    "insecure_http_origin", "INSECURE_HTTP_REFUSED", "KEYED_PROXY_REFUSED", "unsupported_otlp_exporter",
    "insecure_loopback_grpc", "unreadable_tls_file", "otel_env_key_headers", "host_not_allowed",
    "invalid_platform_url", "custom_base_url_not_allowed", "missing_base_url", "insecure_sandbox_origin",
]
NOT_NAMED = ["ambiguous_otlp_endpoint", "insecure_futureagi_http", "insecure_futureagi_grpc",
             "insecure_self_hosted_target", "`proxied`"]


@pytest.mark.parametrize("code", NAMED_ONCE)
def test_a_code_is_named_once(code):
    assert release_section().count(code) == 1


@pytest.mark.parametrize("code", NOT_NAMED)
def test_a_code_the_exporters_do_not_raise_is_not_named(code):
    assert code not in release_section()


def test_the_plain_http_rule_for_future_agi_hosts_is_one_bullet():
    bullets = [b for b in release_section().split("\n- ") if "HTTP exporters (" in b]
    assert len(bullets) == 1 and "INSECURE_HTTP_REFUSED" not in bullets[0]
