"""Redaction before anything is journaled or uploaded, by key and by value shape.

- **By key, failing closed.** A value whose key names a credential becomes ``[redacted]``. Keys are
  matched as words (snake_case, kebab-case, dotted, camelCase), not substrings:
  - ``authorization``, ``secret``, ``password``, ``passphrase``, ``credential``, ``cookie``,
    ``bearer``, ``api_key``, ``private_key``, ``access_key`` anywhere in the key;
  - any word ``key`` / ``keys`` (also run together: ``openaikey``) is a credential (``key``,
    ``openai_key``, ``OPENAI_KEY``, ``azureKey``, ``hf_key``), unless it is a known non-secret name
    (``primary_key``, ``sort_key``, ``cache_key``, ``input_key``, ...) or counts keys
    (``num_keys``, ``key_count``);
  - any word ``token`` / ``tokens`` is a credential (``token``, ``tokens``, ``access_token``,
    ``token_value``, ``auth_tokens``), unless a count word qualifies it (``max_tokens``,
    ``max_new_tokens``, ``prompt_tokens``, ``token_count``, ``tokens_per_minute``) or it names
    tokenizer config (``eos_token``, ``stop_tokens``).
  Wave 0 matched the substrings ``key|token|...`` and blanked ``max_tokens`` in the journaled plan and
  the uploaded ``model_config``; the first fix (the recorded revision) narrowed ``*_key`` to 13 qualifiers and let
  ``openai_key`` through. Unknown names now stay redacted.
- **By value shape**, under a credential key: only values that can carry a secret are replaced:
  strings, bytes, and every such leaf of a dict or list. Numbers, booleans and ``None`` stay, because
  they are config, not secrets (``api_key_set: true``, ``secret_rotation_days: 30``).
- **By key, inside a string** of config: a ``NAME=VALUE`` part whose name is a credential keeps its
  name and loses its value: an argv token such as ``api_key=…`` (``--param api_key=…``),
  ``--token=…``, ``--param=api_key=…``, an eval spec ``judge:api_key=…,model=m`` (only the
  credential's value goes), and a JSON ``"api_key": "…"`` pair inside a ``--param`` value.
- **By value shape**, under any key of config (params, metadata, argv; ``by_key=True``): a string
  shaped like a credential (``Bearer <token>``, OpenAI / Anthropic ``sk-`` keys, Groq ``gsk_``,
  xAI ``xai-``, GitHub ``ghp_`` / ``github_pat_``, AWS ``AKIA…``, Slack ``xox?-``, Google ``AIza…``,
  Hugging Face ``hf_…``, a JWT, a PEM private key) has that part replaced.
- **Known secrets.** Exact matches of secret values known to the process are replaced everywhere
  (outputs, errors, span attributes): values of ``FI_*``, ``*_API_KEY``, ``*_TOKEN``, ``*_SECRET``
  with 8+ chars.
"""

from __future__ import annotations

import os
import re
from typing import Any, Iterable, Mapping, Optional

REDACTED = "[redacted]"
_SECRET_ENV_RE = re.compile(r"^(FI_.*|.*_API_KEY|.*_TOKEN|.*_SECRET|.*_SECRET_KEY|.*_API_SECRET)$")
_MIN_LEN = 8
_NOT_SECRET_ENV = {"FI_BASE_URL", "FI_GRPC_URL", "FI_RUN_DIR", "FI_JUDGE_MODEL", "FI_LOGIN_FILE"}

# credential words that are never config, matched anywhere in the key
_CREDENTIAL_WORDS = re.compile(
    r"authori[sz]ation|secret|passw(?:or)?d|passphrase|credential|cookie|bearer"
    r"|api[_-]?key|private[_-]?key|access[_-]?key",
    re.IGNORECASE,
)
_KEY_PARTS = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")  # snake_case, kebab-case, dotted, camelCase
# a word ending in "key" that is not a credential (a word that ends in "key" is one: "openaikey")
_KEY_ENGLISH = frozenset({"monkey", "donkey", "turkey", "hockey", "jockey", "whiskey", "lackey", "hotkey",
                          "hotkeys", "turnkey", "monkeys", "donkeys", "turkeys"})
# (word, "key"/"keys") or ("key"/"keys", word) pairs that name data, not a credential
_KEY_NOT_SECRET_BEFORE = frozenset({"primary", "foreign", "sort", "partition", "cache", "idempotency", "input",
                                    "output", "group", "join", "dict", "row", "hash", "range", "label", "text",
                                    "lookup", "dedup", "dedupe", "shard", "routing", "index", "unique", "composite",
                                    "map", "column", "field", "message", "record", "item", "object", "metadata"})
_KEY_NOT_SECRET_AFTER = frozenset({"column", "columns", "field", "fields", "name", "names", "order"})
# words that make a "token" / "key" name a count or a limit, not a credential
_TOKEN_COUNT_BEFORE = frozenset({"max", "min", "num", "n", "total", "prompt", "completion", "input", "output",
                                 "cached", "reasoning", "budget", "thinking"})
_TOKEN_COUNT_AFTER = frozenset({"count", "counts", "limit", "limits", "per", "used", "usage", "budget"})
_KEY_COUNT_BEFORE = frozenset({"max", "min", "num", "n", "total"})
_KEY_COUNT_AFTER = frozenset({"count", "counts", "limit", "limits"})
_COUNT_ANYWHERE_BEFORE = frozenset({"max", "min", "num", "total"})  # max_new_tokens, max_output_tokens
# "<word>_token(s)" naming tokenizer config, not a credential (eos_token: "</s>", stop_tokens: [...])
_SPECIAL_TOKENS = frozenset({"eos", "bos", "pad", "sep", "unk", "cls", "mask", "stop", "start", "end", "special"})

_ALNUM = r"[A-Za-z0-9_-]"
_SECRET_SHAPE = re.compile(
    r"(?i:\bbearer)\s+(?=[A-Za-z0-9._~+/=-]*\d)[A-Za-z0-9._~+/=-]{16,}"  # an Authorization header value
    rf"|\bsk-(?={_ALNUM}*\d)(?={_ALNUM}*[A-Z]){_ALNUM}{{20,}}"  # OpenAI sk-, sk-proj-; Anthropic sk-ant-
    r"|\bgsk_(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{20,}"  # Groq
    r"|\bxai-(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{20,}"  # xAI
    r"|\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"  # GitHub
    r"|\bAKIA[0-9A-Z]{16}\b"  # AWS access key id
    r"|\bxox[abposr]-[A-Za-z0-9-]{10,}"  # Slack
    r"|\bAIza[0-9A-Za-z_-]{35}"  # Google API key (Gemini, AI Studio)
    r"|\bhf_(?=[A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*[a-z])[A-Za-z0-9]{30,}"  # Hugging Face
    r"|\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"  # a JWT
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"
)


# NAME= at the start of a string or after "=", ":", ",", "?", "&" (``--param=api_key=…``,
# ``judge:api_key=…``, ``…?token=…``); the value runs to the next such NAME= after "," or "&", else to the end
_NAME_EQ = re.compile(r"(?:^|(?<=[=:,?&]))-{0,2}([A-Za-z_][A-Za-z0-9_.-]*)=")
_JSON_PAIR = re.compile(r'"([^"\\]{1,128})"(\s*:\s*)"((?:[^"\\]|\\.)*)"')  # "name": "value" inside a string


def _counted(parts: list, i: int, before_words: frozenset, after_words: frozenset) -> bool:
    """``parts[i]`` (a key or token word) is a count or a limit: max_tokens, token_count, num_keys."""
    before = parts[i - 1] if i > 0 else None
    after = parts[i + 1] if i + 1 < len(parts) else None
    return (before in before_words or after in after_words
            or any(p in _COUNT_ANYWHERE_BEFORE for p in parts[:i]))


def _key_word(parts: list, i: int) -> bool:
    p = parts[i]
    if p not in ("key", "keys") and not (p.endswith(("key", "keys")) and p not in _KEY_ENGLISH):
        return False
    if p in ("key", "keys"):
        before = parts[i - 1] if i > 0 else None
        after = parts[i + 1] if i + 1 < len(parts) else None
        if before in _KEY_NOT_SECRET_BEFORE or after in _KEY_NOT_SECRET_AFTER:
            return False
    return not _counted(parts, i, _KEY_COUNT_BEFORE, _KEY_COUNT_AFTER)


def _token_word(parts: list, i: int) -> bool:
    p = parts[i]
    if p not in ("token", "tokens") and not p.endswith(("token", "tokens")):
        return False
    if p in ("token", "tokens") and i > 0 and parts[i - 1] in _SPECIAL_TOKENS:
        return False
    return not _counted(parts, i, _TOKEN_COUNT_BEFORE, _TOKEN_COUNT_AFTER)


def is_credential_key(key: str) -> bool:
    """True when ``key`` names a credential. Fails closed: any ``key`` or ``token`` word is a credential
    unless the name is known config (``max_tokens``, ``primary_key``, ``eos_token``)."""
    if _CREDENTIAL_WORDS.search(key):
        return True
    parts = [p.lower() for p in _KEY_PARTS.findall(key)]
    return any(_key_word(parts, i) or _token_word(parts, i) for i in range(len(parts)))


def redact_shapes(value: str) -> str:
    """Replace every part of ``value`` shaped like a credential."""
    return _SECRET_SHAPE.sub(REDACTED, value)


def redact_assignment(value: str) -> str:
    """Every ``NAME=VALUE`` part (or JSON ``"NAME": "VALUE"`` pair) of ``value`` whose name is a
    credential keeps the name and loses the value."""
    if '"' in value:
        value = _JSON_PAIR.sub(
            lambda m: f'"{m.group(1)}"{m.group(2)}"{REDACTED}"' if is_credential_key(m.group(1)) else m.group(0), value)
    if "=" not in value:
        return value
    matches = list(_NAME_EQ.finditer(value))
    out: list[str] = []
    pos = 0
    for i, m in enumerate(matches):
        if m.start() < pos or not is_credential_key(m.group(1)):
            continue
        end = next((n.start() - 1 for n in matches[i + 1:] if value[n.start() - 1:n.start()] in (",", "&")),
                   len(value))
        out += [value[pos:m.end()], REDACTED]
        pos = end
    return "".join(out) + value[pos:] if out else value


def secret_values(environ: Optional[Mapping[str, str]] = None, extra: Iterable[str] = ()) -> list[str]:
    env = os.environ if environ is None else environ
    values = {
        v
        for k, v in env.items()
        if v and len(v) >= _MIN_LEN and k not in _NOT_SECRET_ENV and _SECRET_ENV_RE.match(k)
    }
    values.update(v for v in extra if v and len(v) >= _MIN_LEN)
    # each FI_EXTRA_HEADERS value and the token after its auth scheme ("Bearer <token>"), not only the whole setting
    from fi._extra_headers import secret_values as header_values

    values.update(header_values(env, min_len=_MIN_LEN))
    return sorted(values, key=len, reverse=True)  # longest first, so overlaps redact fully


def client_secret_values(client: Any) -> list[str]:
    """``secret_values()`` plus the header values of a run client's own ``extra_headers=`` (a
    ``FutureAGIClient`` keeps them, checked, on ``_extra_headers``)."""
    extra = getattr(client, "_extra_headers", None)
    argument = getattr(extra, "_argument", None)
    if not argument:
        return secret_values()
    from fi._extra_headers import secret_values as header_values

    return secret_values(extra=header_values({}, extra=[argument], min_len=_MIN_LEN))


def _under_credential_key(value: Any) -> Any:
    """A credential key's value: strings and bytes go, numbers / booleans / None stay."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (str, bytes)):
        return REDACTED if value else value
    if isinstance(value, Mapping):
        return {k: _under_credential_key(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_under_credential_key(v) for v in value]
    return REDACTED  # any other object under a credential key is never journaled as is


class Redactor:
    def __init__(self, secrets: Optional[Iterable[str]] = None) -> None:
        self.secrets = list(secret_values() if secrets is None else secrets)

    def text(self, value: str) -> str:
        for secret in self.secrets:
            if secret in value:
                value = value.replace(secret, REDACTED)
        return value

    def value(self, obj: Any, *, by_key: bool = True) -> Any:
        """Config (``by_key=True``: params, metadata, argv) is redacted by key, by value shape and by
        known secrets; outputs (``by_key=False``) by known secrets only."""
        if isinstance(obj, str):
            return self.text(redact_shapes(redact_assignment(obj)) if by_key else obj)
        if isinstance(obj, Mapping):
            out = {}
            for k, v in obj.items():
                if by_key and isinstance(k, str) and is_credential_key(k):
                    out[k] = _under_credential_key(v)
                else:
                    out[k] = self.value(v, by_key=by_key)
            return out
        if isinstance(obj, (list, tuple)):
            return [self.value(v, by_key=by_key) for v in obj]
        return obj
