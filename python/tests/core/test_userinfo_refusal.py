"""A credentials URL that writes user info is refused, and the refusal names neither the user nor the password."""
from __future__ import annotations

import pytest

from fi._core.http_security import require_secure_credentials_url
from fi.errors import ConfigurationError

USER = "UINFOUSER-3c91d7"
PASS = "UINFOPASS-82e5a0"
ROWS = [USER, f"{USER}:{PASS}", f":{PASS}", f"{USER}%40x", f"{USER}%40x:{PASS}%3A1"]
URLS = ["https://{}@h.example.test/", "http://{}@h.example.test/", "http://{}@127.0.0.1:9/"]


@pytest.mark.parametrize("info", ROWS)
@pytest.mark.parametrize("template", URLS)
@pytest.mark.parametrize("opt_in", [None, True])
def test_user_info_is_refused_without_its_text(info, template, opt_in):
    with pytest.raises(ConfigurationError) as raised:
        require_secure_credentials_url(template.format(info), allow_insecure_http=opt_in, environ={})
    text = f"{raised.value} {raised.value!r} {raised.value.args}"
    for secret in (USER, PASS, USER.lower(), PASS.lower()):
        assert secret not in text
