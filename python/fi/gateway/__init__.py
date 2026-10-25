"""fi.gateway: OpenAI-compatible client for the Future AGI gateway (Agent Command Center).

    from fi.gateway import Gateway
    gw = Gateway()   # FI_GATEWAY_API_KEY / FI_GATEWAY_URL (AGENTCC_* also work)

This is the AgentCC SDK (formerly the separate ``agentcc`` package), vendored
into ``futureagi``. ``AgentCC`` / ``AsyncAgentCC`` keep their original behaviour.
Gateway management (keys, providers, logs) is on ``fi.Client().gateway``.
"""

from __future__ import annotations

from fi.gateway._constants import NOT_GIVEN as NOT_GIVEN
from fi.gateway._constants import __version__ as __version__
from fi.gateway._exceptions import (
    APIConnectionError as APIConnectionError,
)
from fi.gateway._exceptions import (
    APIStatusError as APIStatusError,
)
from fi.gateway._exceptions import (
    APITimeoutError as APITimeoutError,
)
from fi.gateway._exceptions import (
    AuthenticationError as AuthenticationError,
)
from fi.gateway._exceptions import (
    BadGatewayError as BadGatewayError,
)
from fi.gateway._exceptions import (
    BadRequestError as BadRequestError,
)
from fi.gateway._exceptions import (
    GatewayTimeoutError as GatewayTimeoutError,
)
from fi.gateway._exceptions import (
    GuardrailBlockedError as GuardrailBlockedError,
)
from fi.gateway._exceptions import (
    GuardrailWarning as GuardrailWarning,
)
from fi.gateway._exceptions import (
    InternalServerError as InternalServerError,
)
from fi.gateway._exceptions import (
    NotFoundError as NotFoundError,
)
from fi.gateway._exceptions import (
    PermissionDeniedError as PermissionDeniedError,
)
from fi.gateway._exceptions import (
    AgentCCError as AgentCCError,
)
from fi.gateway._exceptions import (
    RateLimitError as RateLimitError,
)
from fi.gateway._exceptions import (
    ServiceUnavailableError as ServiceUnavailableError,
)
from fi.gateway._exceptions import (
    StreamError as StreamError,
)
from fi.gateway._exceptions import (
    UnprocessableEntityError as UnprocessableEntityError,
)

# Lazy imports — these are defined but only loaded when accessed.
# This keeps `import agentcc` fast (<50ms) by deferring httpx/pydantic imports.


def __getattr__(name: str) -> object:
    if name in ("Gateway", "AsyncGateway"):
        from fi.gateway._fi import AsyncGateway, Gateway

        globals()["Gateway"] = Gateway
        globals()["AsyncGateway"] = AsyncGateway
        return globals()[name]

    if name in ("AgentCC", "AsyncAgentCC"):
        from fi.gateway._client import AsyncAgentCC, AgentCC

        globals()["AgentCC"] = AgentCC
        globals()["AsyncAgentCC"] = AsyncAgentCC
        return globals()[name]

    if name in ("Session", "SessionContext"):
        from fi.gateway._session import Session, SessionContext

        globals()["Session"] = Session
        globals()["SessionContext"] = SessionContext
        return globals()[name]

    if name == "Timeout":
        from fi.gateway._base_client import Timeout

        globals()["Timeout"] = Timeout
        return Timeout

    if name in ("Stream", "AsyncStream", "ChunkAccumulator"):
        from fi.gateway._streaming import AsyncStream, ChunkAccumulator, Stream

        globals()["Stream"] = Stream
        globals()["AsyncStream"] = AsyncStream
        globals()["ChunkAccumulator"] = ChunkAccumulator
        return globals()[name]

    if name == "patch_openai":
        from fi.gateway._compat import patch_openai

        globals()["patch_openai"] = patch_openai
        return patch_openai

    if name in (
        "token_counter",
        "get_max_tokens",
        "get_max_output_tokens",
        "completion_cost",
        "completion_cost_from_response",
        "encode",
        "decode",
        "trim_messages",
        "is_prompt_caching_valid",
    ):
        from fi.gateway._tokens import (
            completion_cost,
            completion_cost_from_response,
            decode,
            encode,
            get_max_output_tokens,
            get_max_tokens,
            is_prompt_caching_valid,
            token_counter,
            trim_messages,
        )

        globals()["token_counter"] = token_counter
        globals()["get_max_tokens"] = get_max_tokens
        globals()["get_max_output_tokens"] = get_max_output_tokens
        globals()["completion_cost"] = completion_cost
        globals()["completion_cost_from_response"] = completion_cost_from_response
        globals()["encode"] = encode
        globals()["decode"] = decode
        globals()["trim_messages"] = trim_messages
        globals()["is_prompt_caching_valid"] = is_prompt_caching_valid
        return globals()[name]

    if name == "stream_chunk_builder":
        from fi.gateway._streaming import stream_chunk_builder

        globals()["stream_chunk_builder"] = stream_chunk_builder
        return stream_chunk_builder

    if name in (
        "ModelInfo",
        "get_model_info",
        "MODEL_INFO",
        "validate_environment",
        "get_valid_models",
        "register_model",
        "model_alias_map",
        "supports_vision",
        "supports_function_calling",
        "supports_json_mode",
        "supports_response_schema",
    ):
        from fi.gateway._models_info import (
            MODEL_INFO,
            ModelInfo,
            get_model_info,
            get_valid_models,
            model_alias_map,
            register_model,
            supports_function_calling,
            supports_json_mode,
            supports_response_schema,
            supports_vision,
            validate_environment,
        )

        globals()["ModelInfo"] = ModelInfo
        globals()["get_model_info"] = get_model_info
        globals()["MODEL_INFO"] = MODEL_INFO
        globals()["validate_environment"] = validate_environment
        globals()["get_valid_models"] = get_valid_models
        globals()["register_model"] = register_model
        globals()["model_alias_map"] = model_alias_map
        globals()["supports_vision"] = supports_vision
        globals()["supports_function_calling"] = supports_function_calling
        globals()["supports_json_mode"] = supports_json_mode
        globals()["supports_response_schema"] = supports_response_schema
        return globals()[name]

    if name == "function_to_dict":
        from fi.gateway._function_utils import function_to_dict

        globals()["function_to_dict"] = function_to_dict
        return function_to_dict

    if name == "RetryPolicy":
        from fi.gateway._retry_policy import RetryPolicy

        globals()["RetryPolicy"] = RetryPolicy
        return RetryPolicy

    if name == "BudgetManager":
        from fi.gateway._budget import BudgetManager

        globals()["BudgetManager"] = BudgetManager
        return BudgetManager

    if name in (
        "get_context_window_fallback",
        "get_content_policy_fallback",
        "CONTEXT_WINDOW_FALLBACKS",
        "CONTENT_POLICY_FALLBACKS",
    ):
        from fi.gateway._tokens import (
            CONTENT_POLICY_FALLBACKS,
            CONTEXT_WINDOW_FALLBACKS,
            get_content_policy_fallback,
            get_context_window_fallback,
        )

        globals()["get_context_window_fallback"] = get_context_window_fallback
        globals()["get_content_policy_fallback"] = get_content_policy_fallback
        globals()["CONTEXT_WINDOW_FALLBACKS"] = CONTEXT_WINDOW_FALLBACKS
        globals()["CONTENT_POLICY_FALLBACKS"] = CONTENT_POLICY_FALLBACKS
        return globals()[name]

    if name in ("to_response_format", "validate_json_response"):
        from fi.gateway._structured import to_response_format, validate_json_response

        globals()["to_response_format"] = to_response_format
        globals()["validate_json_response"] = validate_json_response
        return globals()[name]

    if name in ("return_raw_request", "check_valid_key", "health_check"):
        from fi.gateway._utils import check_valid_key, health_check, return_raw_request

        globals()["return_raw_request"] = return_raw_request
        globals()["check_valid_key"] = check_valid_key
        globals()["health_check"] = health_check
        return globals()[name]

    if name in (
        "GatewayConfig",
        "FallbackConfig",
        "FallbackTarget",
        "LoadBalanceConfig",
        "LoadBalanceTarget",
        "CacheConfig",
        "GuardrailConfig",
        "GuardrailCheck",
        "ConditionalRoutingConfig",
        "RoutingCondition",
        "TrafficMirrorConfig",
        "RetryConfig",
        "TimeoutConfig",
        "create_headers",
    ):
        from fi.gateway._gateway_config import (
            CacheConfig,
            ConditionalRoutingConfig,
            FallbackConfig,
            FallbackTarget,
            GatewayConfig,
            GuardrailCheck,
            GuardrailConfig,
            LoadBalanceConfig,
            LoadBalanceTarget,
            RetryConfig,
            RoutingCondition,
            TimeoutConfig,
            TrafficMirrorConfig,
            create_headers,
        )

        globals()["GatewayConfig"] = GatewayConfig
        globals()["FallbackConfig"] = FallbackConfig
        globals()["FallbackTarget"] = FallbackTarget
        globals()["LoadBalanceConfig"] = LoadBalanceConfig
        globals()["LoadBalanceTarget"] = LoadBalanceTarget
        globals()["CacheConfig"] = CacheConfig
        globals()["GuardrailConfig"] = GuardrailConfig
        globals()["GuardrailCheck"] = GuardrailCheck
        globals()["ConditionalRoutingConfig"] = ConditionalRoutingConfig
        globals()["RoutingCondition"] = RoutingCondition
        globals()["TrafficMirrorConfig"] = TrafficMirrorConfig
        globals()["RetryConfig"] = RetryConfig
        globals()["TimeoutConfig"] = TimeoutConfig
        globals()["create_headers"] = create_headers
        return globals()[name]

    if name == "create_mock_client":
        from fi.gateway.testing.mock import create_mock_client

        globals()["create_mock_client"] = create_mock_client
        return create_mock_client

    if name in ("JSONLoggingCallbackHandler", "AgentCCLogger"):
        from fi.gateway.callbacks.custom_logger import AgentCCLogger
        from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler

        globals()["JSONLoggingCallbackHandler"] = JSONLoggingCallbackHandler
        globals()["AgentCCLogger"] = AgentCCLogger
        return globals()[name]

    if name == "AGENTCC_GATEWAY_URL":
        from fi.gateway._constants import AGENTCC_GATEWAY_URL

        globals()["AGENTCC_GATEWAY_URL"] = AGENTCC_GATEWAY_URL
        return AGENTCC_GATEWAY_URL

    if name in (
        "batch_completion",
        "abatch_completion",
        "batch_completion_models",
        "abatch_completion_models",
        "batch_completion_models_all",
        "abatch_completion_models_all",
    ):
        from fi.gateway._batch import (
            abatch_completion,
            abatch_completion_models,
            abatch_completion_models_all,
            batch_completion,
            batch_completion_models,
            batch_completion_models_all,
        )

        globals()["batch_completion"] = batch_completion
        globals()["abatch_completion"] = abatch_completion
        globals()["batch_completion_models"] = batch_completion_models
        globals()["abatch_completion_models"] = abatch_completion_models
        globals()["batch_completion_models_all"] = batch_completion_models_all
        globals()["abatch_completion_models_all"] = abatch_completion_models_all
        return globals()[name]

    raise AttributeError(f"module 'agentcc' has no attribute {name!r}")


__all__ = [
    "Gateway",
    "AsyncGateway",
    "CONTENT_POLICY_FALLBACKS",
    "CONTEXT_WINDOW_FALLBACKS",
    "MODEL_INFO",
    "NOT_GIVEN",
    "AGENTCC_GATEWAY_URL",
    "APIConnectionError",
    "APIStatusError",
    "APITimeoutError",
    "AsyncAgentCC",
    "AsyncStream",
    "AuthenticationError",
    "BadGatewayError",
    "BadRequestError",
    "BudgetManager",
    "CacheConfig",
    "ChunkAccumulator",
    "ConditionalRoutingConfig",
    "FallbackConfig",
    "FallbackTarget",
    "GatewayConfig",
    "GatewayTimeoutError",
    "GuardrailBlockedError",
    "GuardrailCheck",
    "GuardrailConfig",
    "GuardrailWarning",
    "InternalServerError",
    "JSONLoggingCallbackHandler",
    "LoadBalanceConfig",
    "LoadBalanceTarget",
    "ModelInfo",
    "NotFoundError",
    "PermissionDeniedError",
    "AgentCC",
    "AgentCCError",
    "AgentCCLogger",
    "RateLimitError",
    "RetryConfig",
    "RetryPolicy",
    "RoutingCondition",
    "ServiceUnavailableError",
    "Session",
    "SessionContext",
    "Stream",
    "StreamError",
    "Timeout",
    "TimeoutConfig",
    "TrafficMirrorConfig",
    "UnprocessableEntityError",
    "__version__",
    "abatch_completion",
    "abatch_completion_models",
    "abatch_completion_models_all",
    "batch_completion",
    "batch_completion_models",
    "batch_completion_models_all",
    "check_valid_key",
    "completion_cost",
    "completion_cost_from_response",
    "create_headers",
    "create_mock_client",
    "decode",
    "encode",
    "function_to_dict",
    "get_content_policy_fallback",
    "get_context_window_fallback",
    "get_max_output_tokens",
    "get_max_tokens",
    "get_model_info",
    "get_valid_models",
    "health_check",
    "is_prompt_caching_valid",
    "model_alias_map",
    "patch_openai",
    "register_model",
    "return_raw_request",
    "stream_chunk_builder",
    "supports_function_calling",
    "supports_json_mode",
    "supports_response_schema",
    "supports_vision",
    "to_response_format",
    "token_counter",
    "trim_messages",
    "validate_environment",
    "validate_json_response",
]
