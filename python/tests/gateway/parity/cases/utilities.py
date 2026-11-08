"""Pure utilities on fixed inputs (most are S-bucket: shim-only after 2.0)."""

from __future__ import annotations

import copy
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from .._fixtures import MSG, chunks, ok
from .._runner import Case

MODELS_EXTRA = ("unknown-model", "openai/gpt-4o", "gpt-4o-2024-08-06", "")
TEXTS = (
    "",
    "hello world",
    "The quick brown fox jumps over the lazy dog. " * 3,
    "naive cafe 1234 !?",
)
LONG = [{"role": "system", "content": "rules " * 50}] + [
    {"role": "user", "content": f"turn {i} " * 40} for i in range(12)
]
TS = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z")


def _per_model(ctx):
    t = ctx.T
    out = {}
    for model in sorted(t.MODEL_INFO) + list(MODELS_EXTRA):
        out[model] = {
            "info": t.get_model_info(model),
            "max_tokens": t.get_max_tokens(model),
            "max_output_tokens": t.get_max_output_tokens(model),
            "cost_1k_1k": t.completion_cost(
                model, prompt_tokens=1000, completion_tokens=1000
            ),
            "vision": t.supports_vision(model),
            "functions": t.supports_function_calling(model),
            "json_mode": t.supports_json_mode(model),
            "response_schema": t.supports_response_schema(model),
            "context_fallback": t.get_context_window_fallback(model),
            "content_fallback": t.get_content_policy_fallback(model),
            "prompt_caching": t.is_prompt_caching_valid(model, LONG[:2]),
        }
    return out


def _tables(ctx):
    t = ctx.T
    return {
        "valid_models": t.get_valid_models(),
        "context_window_fallbacks": t.CONTEXT_WINDOW_FALLBACKS,
        "content_policy_fallbacks": t.CONTENT_POLICY_FALLBACKS,
        "model_alias_map": dict(t.model_alias_map),
        "model_info_keys": sorted(t.MODEL_INFO),
    }


def _tokens(ctx):
    t = ctx.T
    out = {}
    for model in ("gpt-4o", "claude-3-5-haiku-20241022", "unknown-model"):
        for text in TEXTS:
            encoded = ctx.attempt(lambda: t.encode(model, text))
            out[f"{model}|{text[:20]}"] = {
                "encode": encoded,
                "decode": ctx.attempt(lambda: t.decode(model, [9906, 1917])),
                "count_text": ctx.attempt(lambda: t.token_counter(model, text=text)),
            }
        out[f"{model}|messages"] = ctx.attempt(
            lambda: t.token_counter(model, messages=MSG)
        )
    out["invalid_window"] = ctx.attempt(
        lambda: t.BudgetManager(max_budget=1.0, window="daily")
    )
    return out


def _trim(ctx):
    t = ctx.T
    return {
        "default": t.trim_messages(copy.deepcopy(LONG), "gpt-4o"),
        "max_tokens_50": t.trim_messages(copy.deepcopy(LONG), "gpt-4o", max_tokens=50),
        "ratio_0.1_small_model": t.trim_messages(
            copy.deepcopy(LONG), "gpt-4", trim_ratio=0.1, max_tokens=200
        ),
        "unknown_model": t.trim_messages(
            copy.deepcopy(LONG), "unknown-model", max_tokens=100
        ),
    }


def _register_model(ctx):
    t = ctx.T
    saved = copy.deepcopy(t.MODEL_INFO)
    try:
        t.register_model("parity-model", copy.copy(t.get_model_info("gpt-4o")))
        return {
            "info": t.get_model_info("parity-model"),
            "valid": "parity-model" in t.get_valid_models(),
        }
    finally:
        t.MODEL_INFO.clear()
        t.MODEL_INFO.update(saved)


def _cost_from_response(ctx):
    t = ctx.T
    completion = ctx.mod("testing").make_completion(model="gpt-4o")
    return {
        "from_completion": t.completion_cost_from_response(completion),
        "from_dict": t.completion_cost_from_response(
            {"model": "gpt-4o", "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        ),
    }


def _budget(ctx):
    t = ctx.T
    b = t.BudgetManager(max_budget=1.0, window="1d")
    steps: list[Any] = [b.check_budget(), b.get_remaining_budget()]
    b.update_cost(0.4)
    b.update_cost(0.4, user="u1")
    steps += [
        b.get_current_spend(),
        b.get_remaining_budget(),
        b.check_budget(),
        b.projected_cost(0.3),
    ]
    b.set_user_budget("u1", 0.5)
    steps += [b.is_valid_user("u1"), b.is_valid_user("nobody")]
    b.update_cost(0.5)
    steps += [b.check_budget(), b.get_current_spend()]
    b.reset()
    steps += [b.get_current_spend(), b.max_budget, b.window]
    return [ctx.attempt(lambda s=s: s) for s in steps]


def _structured(ctx):
    t = ctx.T
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int | None = None

    def get_weather(city: str, unit: str = "c", days: int = 1) -> str:
        """Get the weather.

        Args:
            city: City name.
            unit: c or f.
        """
        return city

    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }
    return {
        "to_response_format": t.to_response_format(Person),
        "function_to_dict": t.function_to_dict(get_weather),
        "validate_ok": t.validate_json_response('{"name":"Ada"}', schema),
        "validate_missing": t.validate_json_response("{}", schema),
        "validate_not_json": t.validate_json_response("nope", schema),
    }


def _accumulate(ctx):
    chunk_cls = ctx.mod("types.chat.chat_completion_chunk").ChatCompletionChunk
    out = {}
    for key in ("content", "tool_calls"):
        parsed = [
            chunk_cls.model_validate(json.loads(f))
            for f in chunks(key)
            if f != "[DONE]"
        ]
        acc = ctx.T.ChunkAccumulator()
        for c in parsed:
            acc.add(c)
        out[key] = {
            "accumulator": acc.build(),
            "builder": ctx.T.stream_chunk_builder(parsed),
        }
    out["builder_empty"] = ctx.attempt(lambda: ctx.T.stream_chunk_builder([]))
    return out


def _json_logger(ctx):
    path = Path(tempfile.mkdtemp(prefix="parity-")) / "log.jsonl"
    handler = ctx.T.JSONLoggingCallbackHandler(file_path=str(path))
    client = ctx.client(max_retries=1, callbacks=[handler])
    ctx.attempt(
        lambda: ctx.call(
            client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
        )
    )
    text = path.read_text() if path.exists() else None
    return TS.sub("<timestamp>", text) if text else text


def _raw_request(ctx):
    return ctx.T.return_raw_request(
        model="gpt-4o", messages=MSG, temperature=0.1, session_id="s"
    )


def _patch_openai(ctx):
    client = ctx.T.patch_openai(
        api_key="parity-gateway-key",
        base_url="https://gateway.example.test",
        max_retries=0,
    )
    return {
        "type": type(client).__qualname__,
        "result": ctx.call(
            client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
        ),
    }


def _batch(fn_name: str, *args: Any, **kwargs: Any):
    def fn(ctx):
        client = ctx.client(max_retries=0)
        return ctx.run(
            getattr(ctx.T, fn_name)(client, *args, max_concurrency=1, **kwargs)
        )

    return fn


def _validate_env(ctx):
    return ctx.T.validate_environment()


def cases() -> list[Case]:
    two = [MSG, [{"role": "user", "content": "again"}]]
    models = ["gpt-4o-mini", "claude-3-5-haiku"]
    err = {"status": 400, "json": {"error": {"message": "bad"}}}
    return [
        Case("utility.per_model", "utilities", _per_model),
        Case("utility.tables", "utilities", _tables),
        Case("utility.tokens", "utilities", _tokens),
        Case("utility.trim_messages", "utilities", _trim),
        Case("utility.register_model", "utilities", _register_model),
        Case("utility.cost_from_response", "utilities", _cost_from_response),
        Case("utility.budget_manager", "utilities", _budget),
        Case("utility.structured_output", "utilities", _structured),
        Case("utility.chunk_accumulator", "utilities", _accumulate),
        Case(
            "utility.json_logging_callback",
            "utilities",
            _json_logger,
            replies=[ok("chat_completion", headers={"x-agentcc-cost": "0.1"})],
        ),
        Case("utility.return_raw_request", "utilities", _raw_request),
        Case(
            "utility.patch_openai",
            "utilities",
            _patch_openai,
            replies=[ok("chat_completion")],
        ),
        Case(
            "utility.validate_environment",
            "utilities",
            _validate_env,
            env={"AGENTCC_API_KEY": "parity-gateway-key"},
        ),
        Case("utility.validate_environment.empty", "utilities", _validate_env),
        Case(
            "utility.batch_completion",
            "utilities",
            _batch("batch_completion", "gpt-4o-mini", two),
            replies=[ok("chat_completion")] * 2,
        ),
        Case(
            "utility.batch_completion.errors",
            "utilities",
            _batch("batch_completion", "gpt-4o-mini", two, return_exceptions=True),
            replies=[ok("chat_completion"), err],
        ),
        Case(
            "utility.abatch_completion",
            "utilities",
            _batch("abatch_completion", "gpt-4o-mini", two),
            ("async",),
            replies=[ok("chat_completion")] * 2,
        ),
        Case(
            "utility.batch_completion_models",
            "utilities",
            _batch("batch_completion_models", models, MSG),
            replies=[err, ok("chat_completion")],
        ),
        Case(
            "utility.abatch_completion_models",
            "utilities",
            _batch("abatch_completion_models", models, MSG),
            ("async",),
            replies=[ok("chat_completion")] * 2,
        ),
        Case(
            "utility.batch_completion_models_all",
            "utilities",
            _batch("batch_completion_models_all", models, MSG, return_exceptions=True),
            replies=[ok("chat_completion"), err],
        ),
        Case(
            "utility.abatch_completion_models_all",
            "utilities",
            _batch("abatch_completion_models_all", models, MSG),
            ("async",),
            replies=[ok("chat_completion")] * 2,
        ),
    ]
