"""Type stubs for the agentcc package — enables IDE autocomplete for lazy imports."""

from collections.abc import Callable
from typing import Any

# -- Version & sentinel --

__version__: str
NOT_GIVEN: Any
AGENTCC_GATEWAY_URL: str

# -- Client classes (from _client) --

from fi.gateway._client import AsyncAgentCC as AsyncAgentCC
from fi.gateway._client import AgentCC as AgentCC
from fi.gateway._fi import AsyncGateway as AsyncGateway
from fi.gateway._fi import Gateway as Gateway

# -- Session (from _session) --

from fi.gateway._session import Session as Session
from fi.gateway._session import SessionContext as SessionContext

# -- Timeout (from _base_client) --

from fi.gateway._base_client import Timeout as Timeout

# -- Streaming (from _streaming) --

from fi.gateway._streaming import AsyncStream as AsyncStream
from fi.gateway._streaming import ChunkAccumulator as ChunkAccumulator
from fi.gateway._streaming import Stream as Stream

from fi.gateway.types.chat.chat_completion import ChatCompletion
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

def stream_chunk_builder(chunks: list[ChatCompletionChunk]) -> ChatCompletion: ...

# -- Compat (from _compat) --

def patch_openai(
    client: Any = ...,
    *,
    api_key: str | None = ...,
    base_url: str | None = ...,
    **kwargs: Any,
) -> AgentCC: ...

# -- Token utilities (from _tokens) --

def token_counter(
    model: str,
    text: str | None = ...,
    messages: list[dict[str, Any]] | None = ...,
) -> int: ...

def get_max_tokens(model: str) -> int | None: ...
def get_max_output_tokens(model: str) -> int | None: ...

def completion_cost(
    model: str,
    prompt_tokens: int = ...,
    completion_tokens: int = ...,
) -> float | None: ...

def completion_cost_from_response(response: Any) -> float | None: ...

def encode(model: str, text: str) -> list[int]: ...
def decode(model: str, tokens: list[int]) -> str: ...

def trim_messages(
    messages: list[dict[str, Any]],
    model: str,
    trim_ratio: float = ...,
    max_tokens: int | None = ...,
) -> list[dict[str, Any]]: ...

def is_prompt_caching_valid(
    model: str,
    messages: list[dict[str, Any]],
) -> tuple[bool, str]: ...

# -- Fallback maps (from _tokens) --

CONTEXT_WINDOW_FALLBACKS: dict[str, str]
CONTENT_POLICY_FALLBACKS: dict[str, str]

def get_context_window_fallback(model: str) -> str | None: ...
def get_content_policy_fallback(model: str) -> str | None: ...

# -- Model info (from _models_info) --

from fi.gateway._models_info import ModelInfo as ModelInfo

MODEL_INFO: dict[str, ModelInfo]
model_alias_map: dict[str, str]

def get_model_info(model: str) -> ModelInfo | None: ...
def get_valid_models() -> list[str]: ...
def register_model(model_name: str, model_info: ModelInfo) -> None: ...
def validate_environment() -> dict[str, Any]: ...
def supports_vision(model: str) -> bool: ...
def supports_function_calling(model: str) -> bool: ...
def supports_json_mode(model: str) -> bool: ...
def supports_response_schema(model: str) -> bool: ...

# -- Function utils (from _function_utils) --

def function_to_dict(func: Callable[..., Any]) -> dict[str, Any]: ...

# -- Retry policy (from _retry_policy) --

from fi.gateway._retry_policy import RetryPolicy as RetryPolicy

# -- Budget (from _budget) --

from fi.gateway._budget import BudgetManager as BudgetManager

# -- Structured output (from _structured) --

def to_response_format(model_class: type) -> dict[str, Any]: ...

def validate_json_response(
    response_text: str,
    schema: dict[str, Any],
) -> bool: ...

# -- Utils (from _utils) --

def return_raw_request(
    *,
    model: str,
    messages: list[dict[str, Any]],
    base_url: str = ...,
    **kwargs: Any,
) -> dict[str, Any]: ...

def check_valid_key(api_key: str, base_url: str) -> bool: ...

def health_check(
    model: str | None = ...,
    api_key: str | None = ...,
    base_url: str | None = ...,
    timeout: float = ...,
) -> dict[str, Any]: ...

# -- Gateway configs (from _gateway_config) --

from fi.gateway._gateway_config import CacheConfig as CacheConfig
from fi.gateway._gateway_config import ConditionalRoutingConfig as ConditionalRoutingConfig
from fi.gateway._gateway_config import FallbackConfig as FallbackConfig
from fi.gateway._gateway_config import FallbackTarget as FallbackTarget
from fi.gateway._gateway_config import GatewayConfig as GatewayConfig
from fi.gateway._gateway_config import GuardrailCheck as GuardrailCheck
from fi.gateway._gateway_config import GuardrailConfig as GuardrailConfig
from fi.gateway._gateway_config import LoadBalanceConfig as LoadBalanceConfig
from fi.gateway._gateway_config import LoadBalanceTarget as LoadBalanceTarget
from fi.gateway._gateway_config import RetryConfig as RetryConfig
from fi.gateway._gateway_config import RoutingCondition as RoutingCondition
from fi.gateway._gateway_config import TimeoutConfig as TimeoutConfig
from fi.gateway._gateway_config import TrafficMirrorConfig as TrafficMirrorConfig

def create_headers(
    api_key: str | None = ...,
    config: GatewayConfig | None = ...,
    trace_id: str | None = ...,
    session_id: str | None = ...,
    session_name: str | None = ...,
    session_path: str | None = ...,
    metadata: dict[str, Any] | None = ...,
    user_id: str | None = ...,
    request_id: str | None = ...,
    cache_ttl: int | None = ...,
    cache_namespace: str | None = ...,
    cache_force_refresh: bool | None = ...,
    guardrail_policy: str | None = ...,
    properties: dict[str, str] | None = ...,
) -> dict[str, str]: ...

# -- Mock client (from testing.mock) --

def create_mock_client(
    responses: dict[str, Any] | None = ...,
    api_key: str = ...,
    base_url: str = ...,
) -> Any: ...

# -- Callbacks --

from fi.gateway.callbacks.custom_logger import AgentCCLogger as AgentCCLogger
from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler as JSONLoggingCallbackHandler

# -- Batch utilities (from _batch) --

def batch_completion(
    client: Any,
    model: str,
    messages_list: list[list[dict[str, Any]]],
    max_concurrency: int = ...,
    return_exceptions: bool = ...,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]: ...

async def abatch_completion(
    client: Any,
    model: str,
    messages_list: list[list[dict[str, Any]]],
    max_concurrency: int = ...,
    return_exceptions: bool = ...,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]: ...

def batch_completion_models(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = ...,
    **kwargs: Any,
) -> ChatCompletion: ...

async def abatch_completion_models(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = ...,
    **kwargs: Any,
) -> ChatCompletion: ...

def batch_completion_models_all(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = ...,
    return_exceptions: bool = ...,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]: ...

async def abatch_completion_models_all(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = ...,
    return_exceptions: bool = ...,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]: ...

# -- Exceptions (from _exceptions) --

from fi.gateway._exceptions import APIConnectionError as APIConnectionError
from fi.gateway._exceptions import APIStatusError as APIStatusError
from fi.gateway._exceptions import APITimeoutError as APITimeoutError
from fi.gateway._exceptions import AuthenticationError as AuthenticationError
from fi.gateway._exceptions import BadGatewayError as BadGatewayError
from fi.gateway._exceptions import BadRequestError as BadRequestError
from fi.gateway._exceptions import GatewayTimeoutError as GatewayTimeoutError
from fi.gateway._exceptions import GuardrailBlockedError as GuardrailBlockedError
from fi.gateway._exceptions import GuardrailWarning as GuardrailWarning
from fi.gateway._exceptions import InternalServerError as InternalServerError
from fi.gateway._exceptions import NotFoundError as NotFoundError
from fi.gateway._exceptions import PermissionDeniedError as PermissionDeniedError
from fi.gateway._exceptions import AgentCCError as AgentCCError
from fi.gateway._exceptions import RateLimitError as RateLimitError
from fi.gateway._exceptions import ServiceUnavailableError as ServiceUnavailableError
from fi.gateway._exceptions import StreamError as StreamError
from fi.gateway._exceptions import UnprocessableEntityError as UnprocessableEntityError

# -- __all__ --

__all__: list[str]
