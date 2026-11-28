"""The codes of the refusals that stop a send answer the same text from ``get_error_code()``."""

import pytest

from fi.errors import REFUSAL_CODES, ConfigurationError


@pytest.mark.parametrize("code", ["insecure_channel_origin", "management_credentials", "unsupported_session_adapter"])
def test_a_refusal_code_is_answered_by_get_error_code(code):
    assert code in REFUSAL_CODES
    assert ConfigurationError("refused", code=code).get_error_code() == code


def test_another_code_keeps_the_generic_answer():
    assert ConfigurationError("bad", code="invalid_option").get_error_code() == "CONFIGURATION_ERROR"
