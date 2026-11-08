"""One credential resolver for every platform module and the ``futureagi-py`` CLI.

Order:

1. explicit arguments (``FutureAGIClient(api_key=..., secret_key=..., base_url=...)``);
2. the process environment: ``FI_API_KEY``, ``FI_SECRET_KEY``, ``FI_BASE_URL``;
3. **one** saved login (``$XDG_CONFIG_HOME/futureagi/login.json``), whose keys are bound to the
   base URL saved with them. ``futureagi-py login`` writes it from A6 on; until that command is
   registered, no error message tells users to run it.

The security rules:

- if the base URL comes from anywhere other than the saved login (an argument or
  ``FI_BASE_URL``) and differs from the login's base URL, the saved keys are **not** used. A
  cloned repository can therefore never send your saved keys to its own host;
- keys from arguments or the environment never take the saved login's base URL: without
  ``base_url=`` / ``FI_BASE_URL`` they go to the default (``https://api.futureagi.com``), as
  before. Keys and the server they go to come from one identity.

The platform origin is resolved alongside: ``platform_base_url=``, then
``FI_PLATFORM_BASE_URL``, then the saved login's ``platform_base_url``, else it is **derived** from
the base URL (``{base}/omega/api``). The workspace / organization selectors (``FI_WORKSPACE_ID``,
``FI_ORGANIZATION_ID``) and the self-host Bearer token (``FI_PLATFORM_TOKEN``) resolve the same
way; each value carries its source, which the platform's host guard reads.

The saved login's platform values belong to the identity that saved them: they apply only when
the keys in use are the login's own (``keys_source == "login"``, which also means the login is
bound to the base URL in use). Keys from arguments or the environment never pick up another
user's workspace or origin from the login file. :func:`save_login` stores the derived origin
with a ``platform_base_url_derived`` marker, and a stored origin that is the derived one reads
back as ``derived``, not ``login``, so a login file never changes how the host guard treats it.

This module imports nothing from ``fi.utils`` or ``fi.api``, which other distributions also ship.
Named profiles and the keyring come later.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

from fi.errors import AuthError

API_KEY_ENV = "FI_API_KEY"
SECRET_KEY_ENV = "FI_SECRET_KEY"
BASE_URL_ENV = "FI_BASE_URL"
DEFAULT_BASE_URL = "https://api.futureagi.com"
LOGIN_FILE_ENV = "FI_LOGIN_FILE"  # tests and CI point this somewhere else
PLATFORM_BASE_URL_ENV = "FI_PLATFORM_BASE_URL"
WORKSPACE_ID_ENV = "FI_WORKSPACE_ID"
ORGANIZATION_ID_ENV = "FI_ORGANIZATION_ID"
PLATFORM_TOKEN_ENV = "FI_PLATFORM_TOKEN"
PLATFORM_PATH = "/omega/api"  # path-routed at the ingress, so it derives from the base URL


class CredentialsMissingError(AuthError):
    """No API key / secret key could be resolved (an :class:`fi.errors.AuthError`).

    ``hint`` is one extra sentence a caller adds for its own context: a CLI group names its own
    flag there (``futureagi-py run`` adds ``--no-upload``), so the shared message names no group's
    flag."""

    def __init__(
        self,
        base_url: str,
        missing: tuple[str, ...],
        login_skipped: str | None = None,
        *,
        hint: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.missing = missing
        self.login_skipped = login_skipped
        self.hint = hint
        super().__init__()

    def get_message(self) -> str:
        names = " and ".join(self.missing) or f"{API_KEY_ENV} and {SECRET_KEY_ENV}"
        msg = f"No {names} for {self.base_url}. Set {API_KEY_ENV} and {SECRET_KEY_ENV}, or run `futureagi-py login`."
        if self.hint:
            msg += f" {self.hint}"
        if self.login_skipped:
            msg += f" ({self.login_skipped})"
        return msg

    def get_error_code(self) -> str:
        return "MISSING_AUTH"


class MissingAuthError(CredentialsMissingError):
    """The client could not obtain keys: the name the SDK has always raised.

    It lives here so the clients import it without ``fi.utils``. This distribution's
    ``fi/utils/errors.py`` re-exports it, so there ``from fi.utils.errors import MissingAuthError``
    is the same class. **That holds only while this distribution's ``fi/utils`` is the one on
    disk**: agent-learning-kit and ai-evaluation ship their own ``fi/utils/errors.py`` with their
    own ``MissingAuthError``, and with one of them installed over futureagi,
    ``except fi.utils.errors.MissingAuthError`` no longer catches what the clients raise. Catch
    :class:`fi.errors.AuthError` (or :class:`CredentialsMissingError`) instead.
    """

    def __init__(
        self,
        fi_api_key: Optional[str],
        fi_secret_key: Optional[str],
        cause: Optional[Exception] = None,
        *,
        base_url: Optional[str] = None,
        login_skipped: Optional[str] = None,
    ) -> None:
        self.missing_api_key = fi_api_key is None
        self.missing_secret_key = fi_secret_key is None
        missing = tuple(
            name
            for name, gone in ((API_KEY_ENV, self.missing_api_key), (SECRET_KEY_ENV, self.missing_secret_key))
            if gone
        )
        super().__init__(base_url or "", missing, login_skipped)
        if cause is not None:
            self.__cause__ = cause

    def get_message(self) -> str:
        missing_list = []
        if self.missing_api_key:
            missing_list.append("'fi_api_key'")
        if self.missing_secret_key:
            missing_list.append("'fi_secret_key'")
        msg = (
            "FI Client could not obtain credentials. You can pass your fi_api_key and fi_secret_key "
            "directly to the FI Client, or you can set environment variables which will be read if the "
            "keys are not directly passed. "
            "To set the environment variables use the following variable names: \n"
            f" - {API_KEY_ENV} for the api key\n"
            f" - {SECRET_KEY_ENV} for the secret key\n"
            f"Missing: {', '.join(missing_list)}"
        )
        if self.login_skipped:
            msg += f" ({self.login_skipped})"
        return msg

    def get_error_code(self) -> str:
        return "MISSING_FI_CLIENT_AUTHENTICATION"

    def __repr__(self) -> str:
        return f"MissingAuthError(missing_api_key={self.missing_api_key}, missing_secret_key={self.missing_secret_key})"


@dataclass(frozen=True)
class Credentials:
    api_key: Optional[str] = field(repr=False)
    secret_key: Optional[str] = field(repr=False)
    base_url: str
    keys_source: str  # "argument" | "env" | "login" | "none"
    base_url_source: str  # "argument" | "env" | "login" | "default"
    login_skipped: Optional[str] = None  # why the saved login was not used, if it exists
    # the platform origin and its selectors; each value has its source
    platform_base_url: str = ""
    platform_base_url_source: str = "derived"  # "argument" | "env" | "login" | "derived"
    workspace_id: Optional[str] = None
    workspace_id_source: str = "none"  # "argument" | "env" | "login" | "none"
    organization_id: Optional[str] = None
    organization_id_source: str = "none"
    platform_token: Optional[str] = field(default=None, repr=False)
    platform_token_source: str = "none"  # "argument" | "env" | "none"

    def __post_init__(self) -> None:
        if not self.platform_base_url:
            object.__setattr__(self, "platform_base_url", derive_platform_base_url(self.base_url))

    @property
    def complete(self) -> bool:
        return bool(self.api_key) and bool(self.secret_key)

    def require(self) -> "Credentials":
        if not self.complete:
            missing = tuple(
                n for n, v in ((API_KEY_ENV, self.api_key), (SECRET_KEY_ENV, self.secret_key)) if not v
            )
            raise CredentialsMissingError(self.base_url, missing, self.login_skipped)
        return self

    def describe(self) -> str:
        """One header line, never a key value: ``http://host  (keys from env)``."""
        src = {"argument": "keys from arguments", "env": "keys from env", "login": "keys from saved login"}
        return f"{self.base_url}  ({src.get(self.keys_source, 'no keys')})"


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "futureagi"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "futureagi"


def login_path() -> Path:
    override = os.environ.get(LOGIN_FILE_ENV)
    return Path(override) if override else config_dir() / "login.json"


def load_login(path: Path | None = None) -> Optional[dict]:
    path = path or login_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data.get("base_url"):
        return None
    return data


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def derive_platform_base_url(base_url: str) -> str:
    """The platform origin for a base URL: ``{base_url}/omega/api``. One
    ``FI_BASE_URL`` covers both origins, the hosted default and self-hosted alike."""
    return base_url.strip().rstrip("/") + PLATFORM_PATH


def _pick(
    arg: Optional[str], env: Mapping[str, str], env_name: str, login: Optional[dict], key: str
) -> tuple[Optional[str], str]:
    if arg:
        return arg, "argument"
    if env.get(env_name):
        return env[env_name], "env"
    if login and login.get(key):
        return str(login[key]), "login"
    return None, "none"


def save_login(
    api_key: str,
    secret_key: str,
    base_url: str,
    *,
    platform_base_url: Optional[str] = None,
    workspace_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    path: Path | None = None,
) -> Path:
    """Write the one saved login (mode 0600 in a 0700 directory). The platform origin is stored
    with it, derived from ``base_url`` unless given (``futureagi-py login --base-url URL
    [--platform-base-url URL]``). Returns the path."""
    if not (api_key and secret_key and base_url):
        raise ValueError("save_login needs api_key, secret_key and base_url")
    path = path or login_path()
    base = base_url.strip().rstrip("/")
    derived = derive_platform_base_url(base)
    explicit = (platform_base_url or "").strip().rstrip("/")
    data = {
        "base_url": base,
        "platform_base_url": explicit or derived,
        "api_key": api_key,
        "secret_key": secret_key,
    }
    if not explicit or normalize_url(explicit) == normalize_url(derived):
        data["platform_base_url_derived"] = True  # reads back as "derived"
    if workspace_id:
        data["workspace_id"] = workspace_id
    if organization_id:
        data["organization_id"] = organization_id
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)
    if sys.platform != "win32":
        os.chmod(path, 0o600)
    return path


def resolve(
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    base_url: Optional[str] = None,
    *,
    platform_base_url: Optional[str] = None,
    workspace_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    platform_token: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
    login_file: Path | None = None,
) -> Credentials:
    """Resolve keys, base URL and the platform origin. Never raises; call
    :meth:`Credentials.require` to insist."""
    env = os.environ if environ is None else environ
    login = load_login(login_file)
    keys = _resolve_keys(api_key, secret_key, base_url, env, login)
    # the login's platform values belong to the identity that saved them: only with its own keys
    # (keys_source "login" also means the login is bound to the base URL in use)
    bound = (
        login
        if login
        and keys.keys_source == "login"
        and normalize_url(str(login["base_url"])) == normalize_url(keys.base_url)
        else None
    )
    p_url, p_src = _pick(platform_base_url, env, PLATFORM_BASE_URL_ENV, bound, "platform_base_url")
    if p_src == "login" and p_url and _stored_origin_is_derived(bound, p_url, keys.base_url):
        p_url, p_src = None, "derived"  # re-derived from the base URL in use, and reported as derived
    ws, ws_src = _pick(workspace_id, env, WORKSPACE_ID_ENV, bound, "workspace_id")
    org, org_src = _pick(organization_id, env, ORGANIZATION_ID_ENV, bound, "organization_id")
    token, token_src = _pick(platform_token, env, PLATFORM_TOKEN_ENV, None, "")
    return Credentials(
        keys.api_key,
        keys.secret_key,
        keys.base_url,
        keys.keys_source,
        keys.base_url_source,
        login_skipped=keys.login_skipped,
        platform_base_url=(p_url or "").rstrip("/"),
        platform_base_url_source=p_src if p_url else "derived",
        workspace_id=ws,
        workspace_id_source=ws_src,
        organization_id=org,
        organization_id_source=org_src,
        platform_token=token,
        platform_token_source=token_src,
    )


def _stored_origin_is_derived(login: Optional[dict], stored: str, base_url: str) -> bool:
    """A login's ``platform_base_url`` that ``save_login`` derived (its marker), or that equals the
    derivation for the base URL in use, is reported as ``derived``."""
    if login and login.get("platform_base_url_derived") is True:
        return True
    return normalize_url(stored) == normalize_url(derive_platform_base_url(base_url))


def _resolve_keys(
    api_key: Optional[str],
    secret_key: Optional[str],
    base_url: Optional[str],
    env: Mapping[str, str],
    login: Optional[dict],
) -> Credentials:
    """The key/base-URL resolution (arguments, env, then the bound saved login)."""
    if base_url:
        url, url_src = base_url, "argument"
    elif env.get(BASE_URL_ENV):
        url, url_src = env[BASE_URL_ENV], "env"
    elif login:
        url, url_src = str(login["base_url"]), "login"
    else:
        url, url_src = DEFAULT_BASE_URL, "default"
    url = url.rstrip("/")

    for given, src, pair in (
        (api_key or secret_key, "argument", (api_key, secret_key)),
        (env.get(API_KEY_ENV) or env.get(SECRET_KEY_ENV), "env", (env.get(API_KEY_ENV), env.get(SECRET_KEY_ENV))),
    ):
        if not given:
            continue
        note = None
        if url_src == "login":  # the login's server is used only with the login's own keys (S12)
            note = (
                f"keys from {'arguments' if src == 'argument' else 'the environment'} go to "
                f"{DEFAULT_BASE_URL}; the saved login's server {url} is used only with its own keys "
                f"(set {BASE_URL_ENV} to choose a server)"
            )
            url, url_src = DEFAULT_BASE_URL, "default"
        return Credentials(pair[0], pair[1], url, src, url_src, login_skipped=note)

    skipped = None
    if login:
        bound = str(login["base_url"])
        if url_src in ("argument", "env") and normalize_url(bound) != normalize_url(url):
            skipped = (
                f"the saved login is bound to {bound.rstrip('/')}; its keys are not sent to {url} "
                f"(base URL from {'FI_BASE_URL' if url_src == 'env' else 'base_url='})"
            )
        elif login.get("api_key") and login.get("secret_key"):
            return Credentials(login["api_key"], login["secret_key"], url, "login", url_src)
    return Credentials(None, None, url, "none", url_src, login_skipped=skipped)
