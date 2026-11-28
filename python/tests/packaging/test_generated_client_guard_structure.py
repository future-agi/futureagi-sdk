"""The generator post-hook ``scripts/guard-sdk-client-credentials.py`` judges the structure of the guarded client.

The committed ``client.py`` with code added around the guard text, code that keeps each guard part byte for byte and
sends the token past the check, makes the hook exit non-zero with a reason and leaves the file as it was: a function
that shadows ``require_secure_credentials_url``, a ``setattr`` with a computed name that replaces the guard method, an
``httpx.Client`` bound to another name and called there, ``getattr(self, "token")``, and an ``httpx.stream`` helper.
The committed client passes as it is. The hook needs only the standard library, so these run on every Python leg.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/guard-sdk-client-credentials.py"
COMMITTED = ROOT / "python/fi/generated/openapi_client/client.py"
GUARD_IMPORT_END = "from fi._core.proxy_routing import SdkDirectAsyncTransport, SdkDirectTransport\n"
AUTHENTICATED_ENTER = '    def __enter__(self) -> "AuthenticatedClient":\n'

SHADOWED_GUARD_CALL = '''

def require_secure_credentials_url(*args: Any, **kwargs: Any) -> None:
    """Accept every URL"""
    return None
'''

COMPUTED_SETATTR = '''

setattr(AuthenticatedClient, "_refuse_plain_" + "http_token", lambda self, client: None)
'''

ALIASED_BUILDER = '''    def get_proxied_httpx_client(self, proxy: str) -> httpx.Client:
        """An httpx.Client with the headers of the guarded client, through ``proxy``"""
        build = httpx.Client
        return build(base_url=self._base_url, headers=self.get_httpx_client().headers, proxy=proxy)

'''

GETATTR_TOKEN = '''    def share_token(self) -> None:
        """Put the token into the headers every client of this one sends"""
        self._headers.update({self.auth_header_name: getattr(self, "token")})

'''

STREAM_HELPER = '''    def stream(self, method: str, url: str) -> Any:
        """Stream a response with the token of the guarded client"""
        return httpx.stream(method, self._base_url + url, headers=self.get_httpx_client().headers)

'''


def committed() -> str:
    return COMMITTED.read_text()


def after_guard_import(text: str) -> str:
    source = committed()
    assert source.count(GUARD_IMPORT_END) == 1
    return source.replace(GUARD_IMPORT_END, GUARD_IMPORT_END + text)


def at_end(text: str) -> str:
    return committed() + text


def in_authenticated_client(text: str) -> str:
    source = committed()
    assert source.count(AUTHENTICATED_ENTER) == 1
    return source.replace(AUTHENTICATED_ENTER, text + AUTHENTICATED_ENTER)


def run_guard(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


# (case, source, words of which the hook's output names at least one)
DEFEATING = [
    (
        "shadowed_require_secure_credentials_url",
        lambda: after_guard_import(SHADOWED_GUARD_CALL),
        ("require_secure_credentials_url",),
    ),
    ("setattr_with_a_computed_name", lambda: at_end(COMPUTED_SETATTR), ("setattr",)),
    ("aliased_httpx_client_builder", lambda: in_authenticated_client(ALIASED_BUILDER), ("httpx.client",)),
    ("getattr_of_the_token", lambda: in_authenticated_client(GETATTR_TOKEN), ("getattr",)),
    ("httpx_stream_helper", lambda: in_authenticated_client(STREAM_HELPER), ("httpx.stream",)),
]


@pytest.mark.parametrize(("source", "reasons"), [case[1:] for case in DEFEATING], ids=[case[0] for case in DEFEATING])
def test_hook_refuses_code_around_the_guard_that_sends_the_token_past_it_and_says_why(tmp_path, source, reasons):
    text = source()
    compile(text, "client.py", "exec")
    target = tmp_path / "client.py"
    target.write_text(text)

    result = run_guard(target)
    output = (result.stdout + result.stderr).lower()

    assert result.returncode != 0, f"the hook accepted the file with rc 0; output: {output!r}"
    assert any(reason.lower() in output for reason in reasons), (reasons, output)
    assert target.read_text() == text, "the hook rewrote a file it refused"


def test_hook_accepts_the_committed_client_with_rc_0_and_leaves_it_byte_identical(tmp_path):
    target = tmp_path / "client.py"
    target.write_bytes(COMMITTED.read_bytes())

    result = run_guard(target)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout + result.stderr == ""
    assert target.read_bytes() == COMMITTED.read_bytes()
