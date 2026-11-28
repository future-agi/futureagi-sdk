"""The generator post-hook ``scripts/guard-sdk-client-credentials.py`` guards the generated client or exits non-zero.

``scripts/generate-oss-sdk.sh`` runs the hook on the ``client.py`` that openapi-python-client writes. A clean
generator output becomes the committed ``client.py`` byte for byte, the committed file passes as it is, and a file
that holds the guard only in part (a comment, a builder without the check, an extra builder, the token written into
``self._headers``, a missing import, a guard method with no check in it, ``with_headers`` writing the caller's headers
into a built httpx client as given) makes the hook exit non-zero with a reason and leaves the file as it was.

The fixture ``fixtures/openapi_python_client_0_28_4_client.py.gz`` is the ``client.py`` that
openapi-python-client 0.28.4 generated for this repository, taken from the parent of the commit that added the hook
(generated code, gzip-compressed so the generator's own docstrings stay byte-exact).
"""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/guard-sdk-client-credentials.py"
COMMITTED = ROOT / "python/fi/generated/openapi_client/client.py"
PRISTINE_FIXTURE = Path(__file__).resolve().parent / "fixtures/openapi_python_client_0_28_4_client.py.gz"
PRISTINE_SHA256 = "9fcd38f1df49a6e00f85be8baff74858686a1d711fe465c56128c7d16fff7c73"
AUTHENTICATED = "class AuthenticatedClient"
GUARD_CALL = "            self._refuse_plain_http_token(client)\n"

# A guarded sync builder that writes the token into the shared ``self._headers`` dict.
SELF_HEADERS_BUILDER = '''    def get_httpx_client(self) -> httpx.Client:
        """Get the underlying httpx.Client, constructing a new one if not set"""
        if self._client is None:
            self._headers[self.auth_header_name] = (
                f"{self.prefix} {self.token}" if self.prefix else self.token
            )
            client = httpx.Client(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=self._headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **self._token_httpx_args(SdkDirectTransport),
            )
            self._refuse_plain_http_token(client)
            self._client = client
        return self._client

'''

# A third httpx builder on AuthenticatedClient that sends the token with no check.
THIRD_BUILDER = '''    def get_stream_httpx_client(self) -> httpx.Client:
        """Get an httpx.Client for streamed responses"""
        headers = {**self._headers, self.auth_header_name: f"{self.prefix} {self.token}"}
        self._stream_client = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            **self._httpx_args,
        )
        return self._stream_client

'''

NEUTERED_GUARD = '''    def _refuse_plain_http_token(self, client: httpx.Client | httpx.AsyncClient) -> None:
        """Refuse the token over plain http"""
        return None

'''

COMMENT_LINE = "# self._refuse_plain_http_token(client) is added by scripts/guard-sdk-client-credentials.py\n"


def pristine() -> str:
    data = gzip.decompress(PRISTINE_FIXTURE.read_bytes())
    assert hashlib.sha256(data).hexdigest() == PRISTINE_SHA256
    return data.decode()


def committed() -> str:
    return COMMITTED.read_text()


def run_guard(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def method_span(source: str, name: str) -> tuple[int, int]:
    """Start and end offsets of ``AuthenticatedClient.<name>`` including its trailing blank line."""
    section = source.index(AUTHENTICATED)
    found = re.compile(rf"^    (?:async )?def {re.escape(name)}\(", re.M).search(source, section)
    assert found, f"AuthenticatedClient.{name} is missing from the source"
    following = re.compile(r"^    (?:async def|def|@)", re.M).search(source, found.end())
    end = following.start() if following else len(source)
    return found.start(), end


def replace_method(source: str, name: str, text: str) -> str:
    start, end = method_span(source, name)
    return source[:start] + text + source[end:]


def method_text(source: str, name: str) -> str:
    start, end = method_span(source, name)
    return source[start:end]


def insert_before_method(source: str, name: str, text: str) -> str:
    start, _ = method_span(source, name)
    return source[:start] + text + source[start:]


def edit_in_method(source: str, name: str, old: str, new: str) -> str:
    start, end = method_span(source, name)
    body = source[start:end]
    assert body.count(old) == 1, f"expected one {old.strip()!r} in AuthenticatedClient.{name}"
    return source[:start] + body.replace(old, new) + source[end:]


def pristine_with_guard_name_in_comment() -> str:
    anchor = "from attrs import define, evolve, field\n"
    source = pristine()
    return source.replace(anchor, anchor + COMMENT_LINE, 1)


def pristine_with_guard_method_and_no_guarded_builder() -> str:
    source = pristine()
    guard = method_text(committed(), "_refuse_plain_http_token")
    return insert_before_method(source, "with_headers", guard)


def pristine_with_third_builder() -> str:
    return insert_before_method(pristine(), "__enter__", THIRD_BUILDER)


def committed_with_guard_call_commented_out() -> str:
    return edit_in_method(committed(), "get_httpx_client", GUARD_CALL, "            # " + GUARD_CALL.lstrip())


def committed_with_guard_call_removed_from_sync_builder() -> str:
    return edit_in_method(committed(), "get_httpx_client", GUARD_CALL, "")


def committed_with_async_builder_as_generated() -> str:
    generated = method_text(pristine(), "get_async_httpx_client")
    return replace_method(committed(), "get_async_httpx_client", generated)


def committed_with_third_builder() -> str:
    return insert_before_method(committed(), "__enter__", THIRD_BUILDER)


def committed_with_token_in_self_headers() -> str:
    return replace_method(committed(), "get_httpx_client", SELF_HEADERS_BUILDER)


def committed_without_http_security_import() -> str:
    source = committed()
    stripped, count = re.subn(r"^from fi\._core\.http_security import (?:\([^)]*\)|[^\n]*)\n", "", source, flags=re.M)
    assert count == 1, "expected one fi._core.http_security import in the committed client.py"
    return stripped


def committed_with_neutered_guard() -> str:
    return replace_method(committed(), "_refuse_plain_http_token", NEUTERED_GUARD)


def committed_with_headers_updating_the_built_client_as_given() -> str:
    source = re.sub(
        r"(self\.(?:_client|_async_client)\.headers\.update\()self\._headers_without_token\(headers\)\)",
        r"\1headers)",
        committed(),
    )
    section = source[source.index(AUTHENTICATED):]
    assert section.count("self._client.headers.update(headers)") == 1
    assert section.count("self._async_client.headers.update(headers)") == 1
    return source


# (case, source builder, words of which the hook's output names at least one)
REFUSED = [
    ("pristine_guard_name_only_in_comment", pristine_with_guard_name_in_comment, ("_refuse_plain_http_token", "comment")),
    (
        "pristine_guard_method_without_guarded_builders",
        pristine_with_guard_method_and_no_guarded_builder,
        ("get_httpx_client", "get_async_httpx_client", "httpx.client(", "httpx.asyncclient(", "builder"),
    ),
    (
        "pristine_third_builder",
        pristine_with_third_builder,
        ("get_stream_httpx_client", "_stream_client", "builder"),
    ),
    (
        "committed_guard_call_commented_out",
        committed_with_guard_call_commented_out,
        ("get_httpx_client", "comment", "httpx.client(", "_refuse_plain_http_token"),
    ),
    (
        "committed_guard_call_removed_from_sync_builder",
        committed_with_guard_call_removed_from_sync_builder,
        ("get_httpx_client", "self._client", "httpx.client(", "_refuse_plain_http_token"),
    ),
    (
        "committed_async_builder_without_check",
        committed_with_async_builder_as_generated,
        ("get_async_httpx_client", "_async_client", "httpx.asyncclient(", "_refuse_plain_http_token"),
    ),
    (
        "committed_third_builder",
        committed_with_third_builder,
        ("get_stream_httpx_client", "_stream_client", "builder"),
    ),
    ("committed_token_written_into_self_headers", committed_with_token_in_self_headers, ("self._headers",)),
    ("committed_http_security_import_removed", committed_without_http_security_import, ("import", "http_security")),
    (
        "committed_guard_method_without_check",
        committed_with_neutered_guard,
        ("_refuse_plain_http_token", "require_secure_credentials_url"),
    ),
    (
        "committed_with_headers_updates_the_built_client_as_given",
        committed_with_headers_updating_the_built_client_as_given,
        ("with_headers",),
    ),
]


def test_hook_turns_the_generated_client_into_the_committed_client(tmp_path):
    target = tmp_path / "client.py"
    target.write_text(pristine())

    result = run_guard(target)

    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == COMMITTED.read_bytes()


def test_hook_accepts_the_committed_client_and_leaves_it_byte_identical(tmp_path):
    target = tmp_path / "client.py"
    target.write_bytes(COMMITTED.read_bytes())

    result = run_guard(target)

    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == COMMITTED.read_bytes()


@pytest.mark.parametrize(("source", "reasons"), [case[1:] for case in REFUSED], ids=[case[0] for case in REFUSED])
def test_hook_refuses_a_partial_guard_and_says_why(tmp_path, source, reasons):
    text = source()
    target = tmp_path / "client.py"
    target.write_text(text)

    result = run_guard(target)
    output = (result.stdout + result.stderr).lower()

    assert result.returncode != 0, f"the hook accepted the file with rc 0; output: {output!r}"
    assert any(reason.lower() in output for reason in reasons), (reasons, output)
    assert target.read_text() == text, "the hook rewrote a file it refused"
