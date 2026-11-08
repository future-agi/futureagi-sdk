"""Credential assertions shared by terminal transport tests."""
import pickle
import httpx
SECRET = "synthetic-credential-only"


def assert_safe(error):
    """Check stored state and exception chains, not interpreter stack frames."""
    seen = set()

    def visit(value):
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, (httpx.Request, httpx.Response)):
            from fi.gateway._constants import CREDENTIAL_HEADER_NAMES

            # Original HTTP objects remain reachable; values, not header names,
            # define the privacy boundary. Inspect all headers for key material.
            for name in CREDENTIAL_HEADER_NAMES | {"x-agentcc-config", "x-agentcc-session-id"}:
                if name in value.headers:
                    assert value.headers[name] == "[REDACTED]"
            visit(dict(value.headers))
            assert SECRET not in str(value) + repr(value)
        if isinstance(value, (str, bytes)):
            assert SECRET not in (value.decode(errors="replace") if isinstance(value, bytes) else value)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)
        elif isinstance(value, BaseException):
            visit(vars(value))
            visit(value.args)
            visit(value.__cause__)
            visit(value.__context__)
        elif isinstance(value, httpx.Response):
            visit(vars(value))
    visit(error)
    assert SECRET.encode() not in pickle.dumps(error)
