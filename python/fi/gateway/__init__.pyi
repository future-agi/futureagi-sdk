"""Public gateway exports; re-export implementations so signatures cannot drift."""

from fi.gateway._constants import (
    NOT_GIVEN as NOT_GIVEN,
    __version__ as __version__,
    AGENTCC_GATEWAY_URL as AGENTCC_GATEWAY_URL,
)
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

__all__: list[str]
