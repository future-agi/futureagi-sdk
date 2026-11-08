"""``futureagi-py login`` / ``futureagi-py logout``, and "who you are" for ``doctor``.

One saved login (``fi._credentials.save_login``): the key pair bound to its base URL, mode 0600 in
a 0700 directory, so every platform module and the CLI read the same keys. Keys are read from a
prompt (no echo), from piped stdin (two lines: API key, then secret key), or with ``--from-env``
from ``FI_API_KEY`` / ``FI_SECRET_KEY``. They are never taken as command-line arguments, which
would land in the shell history. Before saving, the keys are checked against the server
(``GET /accounts/user-info/``); refused keys are not saved (``--no-verify`` skips the check).

The server is ``--base-url``, else ``FI_BASE_URL``, else the hosted default, and login prints which
one and why before any request. ``--base-url`` and ``FI_BASE_URL`` naming two different servers is
refused: keys meant for one server are never sent to another, and a login saved for a server other
than ``FI_BASE_URL`` would never be used while ``FI_BASE_URL`` is set.

Windows: the file is written with the same call; a user-only ACL is SDK-53's work (staging
Windows VM), so until then the login file relies on the profile directory's own ACL.
"""

from __future__ import annotations

import getpass
import os
import sys
from typing import Any, Mapping, Optional

from fi._credentials import (
    API_KEY_ENV,
    BASE_URL_ENV,
    DEFAULT_BASE_URL,
    SECRET_KEY_ENV,
    login_path,
    normalize_url,
    save_login,
)
from fi.errors import AuthenticationError, FutureAGIAPIError, FutureAGIError

USER_INFO = "/accounts/user-info/"


class LoginError(FutureAGIError):
    exit_code = 3

    def get_error_code(self) -> str:
        return "LOGIN_FAILED"


def _client(base_url: str, api_key: str, secret_key: str) -> Any:
    from fi.futureagi_client import FutureAGIClient

    return FutureAGIClient(api_key=api_key, secret_key=secret_key, base_url=base_url)


def _name(obj: Any, *keys: str) -> Optional[str]:
    if not isinstance(obj, Mapping):
        return None
    return next((str(obj[k]) for k in keys if obj.get(k)), None)


def who(base_url: str, api_key: str, secret_key: str) -> dict:
    """The authenticated user's ``email``, ``name``, ``organization`` and ``workspace``, read from
    ``GET /accounts/user-info/`` (backend ``UserInfoResponseSerializer``: ``organization`` is an
    object with ``display_name`` / ``name``; the workspace is ``default_workspace_display_name`` /
    ``default_workspace_name``). Raises the platform client's errors, and :class:`LoginError` when
    the server answers without a user object."""
    data = _client(base_url, api_key, secret_key).users.current()
    if isinstance(data, Mapping) and isinstance(data.get("result"), Mapping):
        data = data["result"]
    if not isinstance(data, Mapping) or not (data.get("email") or data.get("id")):
        raise LoginError(f"{base_url}{USER_INFO} answered without a user (is {base_url} a FutureAGI server?)")
    org = data.get("organization")
    return {
        "email": data.get("email"),
        "name": data.get("name"),
        "organization": _name(org, "display_name", "name") or (org if isinstance(org, str) else None),
        "workspace": _name(data, "default_workspace_display_name", "default_workspace_name"),
    }


def login_server(arg_url: Optional[str]) -> tuple[str, str]:
    """``(base URL, why)``: ``--base-url``, else ``FI_BASE_URL``, else the hosted default. Two
    different servers from ``--base-url`` and ``FI_BASE_URL`` are refused."""
    given = (arg_url or "").strip().rstrip("/")
    env = os.environ.get(BASE_URL_ENV, "").strip().rstrip("/")
    if given and env and normalize_url(given) != normalize_url(env):
        raise LoginError(
            f"--base-url {given} and {BASE_URL_ENV}={env} name two different servers; nothing was sent or saved. "
            f"While {BASE_URL_ENV} is set, a login for another server is never used. Unset {BASE_URL_ENV}, "
            "or pass the same URL"
        )
    if given:
        return given, "--base-url"
    if env:
        return env, BASE_URL_ENV
    return DEFAULT_BASE_URL, f"the default; pass --base-url or set {BASE_URL_ENV} for another server"


def describe_who(info: Mapping[str, Any]) -> str:
    parts = [str(info.get("email") or info.get("name") or "an unnamed user")]
    if info.get("organization"):
        parts.append(f"org {info['organization']}")
    if info.get("workspace"):
        parts.append(f"workspace {info['workspace']}")
    return " · ".join(parts)


def _read_keys(args: Any, stdin: Any) -> tuple[str, str]:
    if getattr(args, "from_env", False):
        api, secret = os.environ.get(API_KEY_ENV, ""), os.environ.get(SECRET_KEY_ENV, "")
        if not (api and secret):
            raise LoginError(f"--from-env needs {API_KEY_ENV} and {SECRET_KEY_ENV} in the environment")
        return api, secret
    if stdin.isatty():
        return getpass.getpass("API key: ").strip(), getpass.getpass("Secret key: ").strip()
    lines = [line.strip() for line in stdin.read().splitlines() if line.strip()]
    if len(lines) < 2:
        raise LoginError("pipe two lines on stdin (the API key, then the secret key), or use --from-env")
    return lines[0], lines[1]


def login_command(args: Any) -> int:
    out = getattr(args, "stdout", None) or sys.stdout
    stdin = getattr(args, "stdin", None) or sys.stdin
    base_url, why = login_server(getattr(args, "base_url", None))
    print(f"Server   {base_url}  (from {why})", file=out)  # before any request: where the keys go
    api_key, secret_key = _read_keys(args, stdin)
    if not (api_key and secret_key):
        raise LoginError("both the API key and the secret key are needed")
    line = "not checked (--no-verify)"
    if not getattr(args, "no_verify", False):
        try:
            line = describe_who(who(base_url, api_key, secret_key))
        except (AuthenticationError, FutureAGIAPIError) as exc:
            status = getattr(exc, "status_code", None)
            if status in (401, 403):
                raise LoginError(f"{base_url} refused these keys (HTTP {status}); nothing was saved") from exc
            raise LoginError(f"{base_url} could not confirm the keys (HTTP {status}); nothing was saved") from exc
        except LoginError as exc:
            raise LoginError(f"{exc}; nothing was saved") from exc
    path = save_login(api_key, secret_key, base_url, platform_base_url=getattr(args, "platform_base_url", None),
                      workspace_id=getattr(args, "workspace_id", None))
    print(f"Logged in to {base_url} as {line}", file=out)
    print(f"Saved    {path} (mode 0600). Keys from FI_API_KEY / FI_SECRET_KEY still win over it.", file=out)
    return 0


def logout_command(args: Any) -> int:
    out = getattr(args, "stdout", None) or sys.stdout
    path = login_path()
    if path.exists():
        path.unlink()
        print(f"Removed  {path}", file=out)
    else:
        print(f"No saved login at {path}", file=out)
    return 0


def who_info(args: Any) -> dict:
    """``{"line": ..., "user": {...}}`` or ``{"line": ..., "error": ...}`` for doctor."""
    import httpx

    from fi._credentials import resolve
    from fi._extra_headers import ExtraHeadersError
    from fi.errors import describe_transport_error

    if getattr(args, "offline", False):
        return {"line": "not checked (--offline)", "error": "offline"}
    creds = resolve()
    if not creds.complete:
        return {"line": "not checked (no keys)", "error": "no keys"}
    try:
        user = who(creds.base_url, creds.api_key or "", creds.secret_key or "")
    except (AuthenticationError, FutureAGIAPIError) as exc:
        status = getattr(exc, "status_code", "?")
        return {"line": f"the server refused these keys (HTTP {status})", "error": f"HTTP {status}"}
    except httpx.TransportError as exc:
        url, reason = describe_transport_error(exc, creds.base_url)
        return {"line": f"could not reach {url} ({reason})", "error": reason}
    except LoginError as exc:  # a 200 that is not a user
        return {"line": str(exc), "error": "not a user"}
    except ExtraHeadersError:  # doctor's Headers line already says what is wrong (never a value)
        return {"line": "not checked (FI_EXTRA_HEADERS is malformed)", "error": "extra headers"}
    return {"line": describe_who(user), "user": user}


def register(subparsers: Any) -> None:
    p = subparsers.add_parser("login", help="save one login (keys bound to their server) for every command")
    p.add_argument("--base-url", dest="base_url", metavar="URL",
                   help=f"the server (default {BASE_URL_ENV}, else {DEFAULT_BASE_URL})")
    p.add_argument("--platform-base-url", dest="platform_base_url", metavar="URL",
                   help="the platform origin, when it is not {base-url}/omega/api")
    p.add_argument("--workspace-id", dest="workspace_id", metavar="ID", help="the workspace to select")
    p.add_argument("--from-env", dest="from_env", action="store_true",
                   help=f"save {API_KEY_ENV} / {SECRET_KEY_ENV} from the environment instead of prompting")
    p.add_argument("--no-verify", dest="no_verify", action="store_true", help="save without checking the keys")
    p.set_defaults(func=login_command)
    q = subparsers.add_parser("logout", help="remove the saved login")
    q.set_defaults(func=logout_command)
