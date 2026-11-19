"""Lazy gateway clients and utilities.

``AgentCC`` requires an explicit gateway origin (argument or environment).
``Gateway`` retains the released fixed HTTPS hosted default. Neither client
uses the platform FI key pair as a gateway virtual key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fi.gateway._constants import NOT_GIVEN as NOT_GIVEN
from fi.gateway._constants import __version__ as __version__
from fi.gateway._exceptions import (
    AgentBudgetExhaustedError as AgentBudgetExhaustedError,
    AgentCCError as AgentCCError,
    APIConnectionError as APIConnectionError,
    APIStatusError as APIStatusError,
    APITimeoutError as APITimeoutError,
    AuthenticationError as AuthenticationError,
    BadGatewayError as BadGatewayError,
    BadRequestError as BadRequestError,
    BudgetExceededError as BudgetExceededError,
    FutureAGICreditsOffError as FutureAGICreditsOffError,
    GatewayTimeoutError as GatewayTimeoutError,
    GuardrailBlockedError as GuardrailBlockedError,
    GuardrailWarning as GuardrailWarning,
    InsufficientCreditsError as InsufficientCreditsError,
    InternalServerError as InternalServerError,
    NotFoundError as NotFoundError,
    PermissionDeniedError as PermissionDeniedError,
    RateLimitError as RateLimitError,
    ServiceUnavailableError as ServiceUnavailableError,
    StreamError as StreamError,
    UnprocessableEntityError as UnprocessableEntityError,
)

if TYPE_CHECKING:
    from fi.gateway._gateway_evidence import DispatchState as DispatchState, GatewayEvidence as GatewayEvidence
    from fi.gateway._base_client import Timeout as Timeout
    from fi.gateway._batch import (
        abatch_completion as abatch_completion,
        abatch_completion_models as abatch_completion_models,
        abatch_completion_models_all as abatch_completion_models_all,
        batch_completion as batch_completion,
        batch_completion_models as batch_completion_models,
        batch_completion_models_all as batch_completion_models_all,
    )
    from fi.gateway._budget import BudgetManager as BudgetManager
    from fi.gateway._client import AgentCC as AgentCC, AsyncAgentCC as AsyncAgentCC
    from fi.gateway._compat import patch_openai as patch_openai
    from fi.gateway._compat_openai import openai_kwargs as openai_kwargs
    from fi.gateway._constants import AGENTCC_GATEWAY_URL as AGENTCC_GATEWAY_URL
    from fi.gateway._deprecation import AgentCCDeprecationWarning as AgentCCDeprecationWarning
    from fi.gateway._fi import Gateway as Gateway, AsyncGateway as AsyncGateway
    from fi.gateway._function_utils import function_to_dict as function_to_dict
    from fi.gateway._gateway_config import (
        CacheConfig as CacheConfig,
        ConditionalRoutingConfig as ConditionalRoutingConfig,
        FallbackConfig as FallbackConfig,
        FallbackTarget as FallbackTarget,
        GatewayConfig as GatewayConfig,
        GuardrailCheck as GuardrailCheck,
        GuardrailConfig as GuardrailConfig,
        LoadBalanceConfig as LoadBalanceConfig,
        LoadBalanceTarget as LoadBalanceTarget,
        RetryConfig as RetryConfig,
        RoutingCondition as RoutingCondition,
        TimeoutConfig as TimeoutConfig,
        TrafficMirrorConfig as TrafficMirrorConfig,
        create_headers as create_headers,
    )
    from fi.gateway._models_info import (
        MODEL_INFO as MODEL_INFO,
        ModelInfo as ModelInfo,
        get_model_info as get_model_info,
        get_valid_models as get_valid_models,
        model_alias_map as model_alias_map,
        register_model as register_model,
        supports_function_calling as supports_function_calling,
        supports_json_mode as supports_json_mode,
        supports_response_schema as supports_response_schema,
        supports_vision as supports_vision,
        validate_environment as validate_environment,
    )
    from fi.gateway._retry_policy import RetryPolicy as RetryPolicy
    from fi.gateway._session import Session as Session, SessionContext as SessionContext
    from fi.gateway._streaming import (
        AsyncStream as AsyncStream,
        ChunkAccumulator as ChunkAccumulator,
        Stream as Stream,
        stream_chunk_builder as stream_chunk_builder,
    )
    from fi.gateway._structured import (
        to_response_format as to_response_format,
        validate_json_response as validate_json_response,
    )
    from fi.gateway._tokens import (
        CONTENT_POLICY_FALLBACKS as CONTENT_POLICY_FALLBACKS,
        CONTEXT_WINDOW_FALLBACKS as CONTEXT_WINDOW_FALLBACKS,
        completion_cost as completion_cost,
        completion_cost_from_response as completion_cost_from_response,
        decode as decode,
        encode as encode,
        get_content_policy_fallback as get_content_policy_fallback,
        get_context_window_fallback as get_context_window_fallback,
        get_max_output_tokens as get_max_output_tokens,
        get_max_tokens as get_max_tokens,
        is_prompt_caching_valid as is_prompt_caching_valid,
        token_counter as token_counter,
        trim_messages as trim_messages,
    )
    from fi.gateway._utils import (
        check_valid_key as check_valid_key,
        health_check as health_check,
        return_raw_request as return_raw_request,
    )
    from fi.gateway.callbacks.custom_logger import AgentCCLogger as AgentCCLogger
    from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler as JSONLoggingCallbackHandler
    from fi.gateway.testing.mock import create_mock_client as create_mock_client
    from fi.gateway.types.agentcc_metadata import (
        AgentCCMetadata as AgentCCMetadata,
        RateLimitInfo as RateLimitInfo,
    )

_LAZY: dict[str, str] = {
    "GatewayEvidence": "fi.gateway._gateway_evidence",
    "DispatchState": "fi.gateway._gateway_evidence",
    "AgentCC": "fi.gateway._client",
    "AsyncAgentCC": "fi.gateway._client",
    "Gateway": "fi.gateway._fi",
    "AsyncGateway": "fi.gateway._fi",
    "Session": "fi.gateway._session",
    "SessionContext": "fi.gateway._session",
    "Timeout": "fi.gateway._base_client",
    "RetryPolicy": "fi.gateway._retry_policy",
    "BudgetManager": "fi.gateway._budget",
    "Stream": "fi.gateway._streaming",
    "AsyncStream": "fi.gateway._streaming",
    "ChunkAccumulator": "fi.gateway._streaming",
    "stream_chunk_builder": "fi.gateway._streaming",
    "create_headers": "fi.gateway._gateway_config",
    "GatewayConfig": "fi.gateway._gateway_config",
    "CacheConfig": "fi.gateway._gateway_config",
    "TimeoutConfig": "fi.gateway._gateway_config",
    "ConditionalRoutingConfig": "fi.gateway._gateway_config",
    "FallbackConfig": "fi.gateway._gateway_config",
    "FallbackTarget": "fi.gateway._gateway_config",
    "GuardrailCheck": "fi.gateway._gateway_config",
    "GuardrailConfig": "fi.gateway._gateway_config",
    "LoadBalanceConfig": "fi.gateway._gateway_config",
    "LoadBalanceTarget": "fi.gateway._gateway_config",
    "RetryConfig": "fi.gateway._gateway_config",
    "RoutingCondition": "fi.gateway._gateway_config",
    "TrafficMirrorConfig": "fi.gateway._gateway_config",
    "create_mock_client": "fi.gateway.testing.mock",
    "health_check": "fi.gateway._utils",
    "check_valid_key": "fi.gateway._utils",
    "return_raw_request": "fi.gateway._utils",
    "to_response_format": "fi.gateway._structured",
    "validate_json_response": "fi.gateway._structured",
    "function_to_dict": "fi.gateway._function_utils",
    "openai_kwargs": "fi.gateway._compat_openai",
    "patch_openai": "fi.gateway._compat",
    "AgentCCDeprecationWarning": "fi.gateway._deprecation",
    "AgentCCMetadata": "fi.gateway.types.agentcc_metadata",
    "RateLimitInfo": "fi.gateway.types.agentcc_metadata",
    "AgentCCLogger": "fi.gateway.callbacks.custom_logger",
    "JSONLoggingCallbackHandler": "fi.gateway.callbacks.json_logger",
    "AGENTCC_GATEWAY_URL": "fi.gateway._constants",
    "batch_completion": "fi.gateway._batch",
    "abatch_completion": "fi.gateway._batch",
    "batch_completion_models": "fi.gateway._batch",
    "abatch_completion_models": "fi.gateway._batch",
    "batch_completion_models_all": "fi.gateway._batch",
    "abatch_completion_models_all": "fi.gateway._batch",
    "MODEL_INFO": "fi.gateway._models_info",
    "ModelInfo": "fi.gateway._models_info",
    "get_model_info": "fi.gateway._models_info",
    "get_valid_models": "fi.gateway._models_info",
    "model_alias_map": "fi.gateway._models_info",
    "register_model": "fi.gateway._models_info",
    "supports_function_calling": "fi.gateway._models_info",
    "supports_json_mode": "fi.gateway._models_info",
    "supports_response_schema": "fi.gateway._models_info",
    "supports_vision": "fi.gateway._models_info",
    "validate_environment": "fi.gateway._models_info",
    "CONTENT_POLICY_FALLBACKS": "fi.gateway._tokens",
    "CONTEXT_WINDOW_FALLBACKS": "fi.gateway._tokens",
    "completion_cost": "fi.gateway._tokens",
    "completion_cost_from_response": "fi.gateway._tokens",
    "decode": "fi.gateway._tokens",
    "encode": "fi.gateway._tokens",
    "get_content_policy_fallback": "fi.gateway._tokens",
    "get_context_window_fallback": "fi.gateway._tokens",
    "get_max_output_tokens": "fi.gateway._tokens",
    "get_max_tokens": "fi.gateway._tokens",
    "is_prompt_caching_valid": "fi.gateway._tokens",
    "token_counter": "fi.gateway._tokens",
    "trim_messages": "fi.gateway._tokens",
}

__all__ = [
    "NOT_GIVEN", "__version__", "AgentCCError", "APIConnectionError",
    "APIStatusError", "APITimeoutError", "AuthenticationError", "BadGatewayError",
    "BadRequestError", "GatewayTimeoutError", "GuardrailBlockedError",
    "GuardrailWarning", "InternalServerError", "NotFoundError",
    "PermissionDeniedError", "RateLimitError", "ServiceUnavailableError",
    "StreamError", "UnprocessableEntityError", "InsufficientCreditsError",
    "AgentBudgetExhaustedError", "BudgetExceededError", "FutureAGICreditsOffError", *_LAZY,
]


_DEPRECATED_RELEASE_NAMES = {
    "AGENTCC_GATEWAY_URL", "AgentCCLogger", "AsyncGateway", "BudgetManager",
    "CONTENT_POLICY_FALLBACKS", "CONTEXT_WINDOW_FALLBACKS", "ConditionalRoutingConfig",
    "FallbackConfig", "FallbackTarget", "Gateway", "GuardrailCheck", "GuardrailConfig",
    "JSONLoggingCallbackHandler", "LoadBalanceConfig", "LoadBalanceTarget", "MODEL_INFO",
    "ModelInfo", "RetryConfig", "RoutingCondition", "TrafficMirrorConfig",
    "abatch_completion", "abatch_completion_models", "abatch_completion_models_all",
    "batch_completion", "batch_completion_models", "batch_completion_models_all",
    "completion_cost", "completion_cost_from_response", "decode", "encode",
    "get_content_policy_fallback", "get_context_window_fallback", "get_max_output_tokens",
    "get_max_tokens", "get_model_info", "get_valid_models", "is_prompt_caching_valid",
    "model_alias_map", "patch_openai", "register_model", "return_raw_request",
    "supports_function_calling", "supports_json_mode", "supports_response_schema",
    "supports_vision", "token_counter", "trim_messages", "validate_environment",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY.get(name)
    if module_name is None:
        raise AttributeError(f"module 'fi.gateway' has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module_name), name)
    if name in _DEPRECATED_RELEASE_NAMES:
        import warnings

        warnings.warn(
            f"fi.gateway.{name} is a deprecated released compatibility API.",
            DeprecationWarning, stacklevel=2,
        )
    else:
        globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(__all__) | {n for n in globals() if n.startswith("__")})
