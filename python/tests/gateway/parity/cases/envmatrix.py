"""Credential and base-URL resolution, FI_* / OPENAI_* isolation, URL shapes.

The TypeScript twin (gateway-client/tests/parity/cases/client-extras.mjs) uses
the same ids and values; test_parity_twins.py holds the two to each other."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from .._fixtures import MSG, ok
from .._runner import ENV_PREFIXES, KEY, Case, omit

BOTH = ("sync", "async")
URL = "https://gateway.example.test"
KEY_SOURCES: dict[str, tuple[dict[str, Any], dict[str, str]]] = {
    "none": ({"api_key": omit()}, {}),
    "arg": ({"api_key": "key-from-arg"}, {}),
    "agentcc_env": ({"api_key": omit()}, {"AGENTCC_API_KEY": "key-from-agentcc-env"}),
    "fi_gateway_env": (
        {"api_key": omit()},
        {"FI_GATEWAY_API_KEY": "key-from-fi-gateway-env"},
    ),
    "both_env_differ": (
        {"api_key": omit()},
        {"AGENTCC_API_KEY": "key-agentcc", "FI_GATEWAY_API_KEY": "key-fi-gateway"},
    ),
    "arg_over_env": (
        {"api_key": "key-from-arg"},
        {"AGENTCC_API_KEY": "key-env", "FI_GATEWAY_API_KEY": "key-fi-env"},
    ),
    "empty_arg_env": ({"api_key": ""}, {"AGENTCC_API_KEY": "key-from-agentcc-env"}),
}
URL_SOURCES: dict[str, tuple[dict[str, Any], dict[str, str]]] = {
    "none": ({"base_url": omit()}, {}),
    "arg": ({"base_url": URL}, {}),
    "agentcc_env": (
        {"base_url": omit()},
        {"AGENTCC_BASE_URL": "https://agentcc-env.example.test"},
    ),
    "fi_gateway_env": (
        {"base_url": omit()},
        {"FI_GATEWAY_BASE_URL": "https://fi-env.example.test"},
    ),
    "both_env_differ": (
        {"base_url": omit()},
        {
            "AGENTCC_BASE_URL": "https://agentcc-env.example.test",
            "FI_GATEWAY_BASE_URL": "https://fi-env.example.test",
        },
    ),
    "arg_over_env": (
        {"base_url": URL},
        {"AGENTCC_BASE_URL": "https://agentcc-env.example.test"},
    ),
    "gateway_url_env": (
        {"base_url": omit()},
        {"AGENTCC_GATEWAY_URL": "https://gateway-url-env.example.test"},
    ),
    "empty_arg_env": (
        {"base_url": ""},
        {"AGENTCC_BASE_URL": "https://agentcc-env.example.test"},
    ),
}
URL_SHAPES = {
    "trailing_slash": URL + "/",
    "v1": URL + "/v1",
    "v1_slash": URL + "/v1/",
    "v1_twice": URL + "/v1/v1",
    "prefix": URL + "/gw",
    "prefix_v1": URL + "/gw/v1",
    "port": "http://127.0.0.1:8090",
    "localhost": "http://localhost:8090",
    "uppercase_v1": URL + "/V1",
}
# The module-level AGENTCC_GATEWAY_URL is read once, at import. The TypeScript
# twin reads AGENTCC_GATEWAY_URL, then AGENTCC_BASE_URL; Python only the latter.
GATEWAY_URL_CONSTANT = {
    "unset": {},
    "agentcc_base_url": {"AGENTCC_BASE_URL": "https://from-env.example.test"},
    "agentcc_gateway_url": {
        "AGENTCC_GATEWAY_URL": "https://gateway-url-env.example.test"
    },
    "both": {
        "AGENTCC_GATEWAY_URL": "https://gateway-url-env.example.test",
        "AGENTCC_BASE_URL": "https://from-env.example.test",
    },
}
ISOLATION_ENV = {
    "FI_API_KEY": "fi-api-key-value",
    "FI_SECRET_KEY": "fi-secret-key-value",
    "FI_BASE_URL": "https://platform.example.test",
    "FI_PLATFORM_TOKEN": "fi-platform-token-value",
    "FI_WORKSPACE_ID": "ws-1",
    "FI_ORGANIZATION_ID": "org-1",
    "OPENAI_API_KEY": "openai-key-value",
    "OPENAI_ORG_ID": "org-openai",
    "OPENAI_PROJECT_ID": "proj-openai",
    "OPENAI_BASE_URL": "https://openai-env.example.test/v1",
}


def _resolve(key_opts: dict[str, Any], url_opts: dict[str, Any]):
    def fn(ctx):
        client = ctx.client(max_retries=0, **key_opts, **url_opts)
        return ctx.call(client, "models.list")

    return fn


def _shape(url: str):
    def fn(ctx):
        client = ctx.client(max_retries=0, base_url=url)
        a = ctx.call(
            client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
        )
        b = ctx.call(client, "models.retrieve", "gpt-4o-mini")
        return [a.id, b.id]

    return fn


def _fi_key_as_gateway_key(ctx):
    client = ctx.client(max_retries=0, api_key=omit())
    return ctx.call(
        client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
    )


def _import_time_gateway_url(env: dict[str, str]):
    def fn(ctx):
        clean = {k: v for k, v in os.environ.items() if not k.startswith(ENV_PREFIXES)}
        clean.update(env)
        code = f"import {ctx.root} as m; print(getattr(m, 'AGENTCC_GATEWAY_URL', '<absent>'))"
        done = subprocess.run(
            [sys.executable, "-c", code],
            env=clean,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "exit": done.returncode,
            "stdout": done.stdout.strip(),
            "stderr_tail": done.stderr.strip().splitlines()[-1:],
        }

    return fn


def cases() -> list[Case]:
    out = []
    for kname, (kopts, kenv) in KEY_SOURCES.items():
        for uname, (uopts, uenv) in URL_SOURCES.items():
            out.append(
                Case(
                    f"env.key_{kname}.url_{uname}",
                    "env_matrix",
                    _resolve(kopts, uopts),
                    ("sync",),
                    env={**kenv, **uenv},
                    replies=[ok("models_list")],
                )
            )
    for name in ("arg", "agentcc_env"):
        kopts, kenv = KEY_SOURCES[name]
        out.append(
            Case(
                f"env.async.key_{name}",
                "env_matrix",
                _resolve(kopts, {}),
                ("async",),
                env=kenv,
                replies=[ok("models_list")],
            )
        )
    for name, url in URL_SHAPES.items():
        out.append(
            Case(
                f"env.base_url.{name}",
                "env_matrix",
                _shape(url),
                BOTH,
                replies=[ok("chat_completion"), ok("model")],
            )
        )
    out.append(
        Case(
            "env.isolation.all_fi_openai_set",
            "env_matrix",
            _resolve({}, {}),
            BOTH,
            env=ISOLATION_ENV,
            replies=[ok("models_list")],
        )
    )
    out.append(
        Case(
            "env.isolation.chat",
            "env_matrix",
            lambda c: c.call(
                c.client(max_retries=0),
                "chat.completions.create",
                model="gpt-4o-mini",
                messages=MSG,
                stream=False,
            ),
            BOTH,
            env=ISOLATION_ENV,
            replies=[ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "env.fi_api_key_reused_as_gateway_key",
            "env_matrix",
            _fi_key_as_gateway_key,
            BOTH,
            env={"FI_API_KEY": KEY, "AGENTCC_API_KEY": KEY},
            replies=[ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "env.fi_secret_key_reused_as_gateway_key",
            "env_matrix",
            _fi_key_as_gateway_key,
            BOTH,
            env={"FI_SECRET_KEY": KEY, "AGENTCC_API_KEY": KEY},
            replies=[ok("chat_completion")],
        )
    )
    for name, env in GATEWAY_URL_CONSTANT.items():
        out.append(
            Case(
                f"env.gateway_url_constant.{name}",
                "env_matrix",
                _import_time_gateway_url(env),
            )
        )
    return out
