import time
from typing import Dict, List, Optional, Union

from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
# Published 0.6.13 imports remain aliases of their canonical definitions.
from fi.api.types import HttpMethod, RequestConfig
from fi.utils.routes import Routes
from fi.errors import PlatformNotConfiguredError
from fi.utils.constants import (
    MAX_FUTURE_YEARS_FROM_CURRENT_TIME,
    MAX_PAST_YEARS_FROM_CURRENT_TIME,
)
from fi.utils.errors import InvalidSupportedType, InvalidValueType, MissingRequiredKey
from fi.utils.logging import logger
from fi.utils.types import Environments, ModelTypes
from fi.utils.utils import is_timestamp_in_range


class ClientResponseHandler(ResponseHandler[Dict, None]):
    """Handles responses for client requests"""

    @classmethod
    def _parse_success(cls, response: Response) -> Dict:
        """Parse successful response

        Args:
            response: Response object from request

        Returns:
            Dict: Parsed JSON response with default status
        """
        data = response.json()
        # Add status if not present in response
        if "status" not in data:
            data["status"] = "success" if response.ok else "error"
        return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        """Handle error response

        Args:
            response: Response object from request

        Raises:
            HTTPError: If response indicates an error
        """
        response.raise_for_status()


class Client(APIKeyAuth):
    """Legacy model-logging client; ``log`` is unsupported on the current platform."""

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize the Fi Client

        Args:
            fi_api_key: API key for authentication
            fi_secret_key: Secret key for authentication
            fi_base_url: Base URL for API requests

        Keyword Args:
            timeout: Default timeout for requests (default: 200)
            additional_headers: Additional headers to include in requests
            max_workers: Maximum number of workers for concurrent requests (default: 8)
            max_queue_size: Maximum size of the request queue (default: 5000)
        """
        super().__init__(fi_api_key, fi_secret_key, fi_base_url, **kwargs)

    def _validate_params(
        self,
        model_id: str,
        model_type: ModelTypes,
        environment: Environments,
        model_version: Optional[str] = None,
        prediction_timestamp: Optional[int] = None,
        conversation: Optional[Dict[str, Union[str, bool, float, int]]] = None,
        tags: Optional[Dict[str, Union[str, bool, float, int]]] = None,
    ) -> None:
        """Validate input parameters

        Args:
            model_id: Model identifier
            model_type: Type of model
            environment: Deployment environment
            model_version: Optional model version
            prediction_timestamp: Optional prediction timestamp
            conversation: Optional conversation data
            tags: Optional tags

        Raises:
            InvalidValueType: If parameter types are invalid
            InvalidSupportedType: If model type is not supported
            MissingRequiredKey: If required keys are missing
            ValueError: If timestamp is out of valid range
        """
        # Validate model id
        if not isinstance(model_id, str):
            raise InvalidValueType("model_id", model_id, "str")

        # Validate model type
        if not isinstance(model_type, ModelTypes):
            raise InvalidValueType(
                "model_type", model_type, "fi.utils.types.ModelTypes"
            )

        # Validate supported model types
        if model_type not in [ModelTypes.GENERATIVE_LLM, ModelTypes.GENERATIVE_IMAGE]:
            raise InvalidSupportedType(
                "model_type",
                model_type,
                "ModelTypes.GENERATIVE_LLM,ModelTypes.GENERATIVE_IMAGE",
            )

        # Validate environment
        if not isinstance(environment, Environments):
            raise InvalidValueType(
                "environment", environment, "fi.utils.types.Environments"
            )

        # Validate model_version
        if model_version and not isinstance(model_version, str):
            raise InvalidValueType("model_version", model_version, "str")

        self._validate_conversation(conversation)
        self._validate_tags(tags)
        self._validate_timestamp(prediction_timestamp)

    def _validate_conversation(
        self, conversation: Optional[Dict[str, Union[str, bool, float, int]]]
    ) -> None:
        """Validate conversation structure and content"""
        if not conversation:
            return

        if not isinstance(conversation, dict):
            raise InvalidValueType("conversation", conversation, "dict")

        if "chat_history" not in conversation and "chat_graph" not in conversation:
            raise MissingRequiredKey("conversation", "[chat_history, chat_graph]")

        if "chat_history" in conversation:
            self._validate_chat_history(conversation["chat_history"])

        if "chat_graph" in conversation:
            self._validate_chat_graph(conversation["chat_graph"])

    def _validate_tags(
        self, tags: Optional[Dict[str, Union[str, bool, float, int]]]
    ) -> None:
        """Validate tags structure and content"""
        if not tags:
            return

        if not isinstance(tags, dict):
            raise InvalidValueType("tags", tags, "dict")

        for key, value in tags.items():
            if not isinstance(key, str):
                raise InvalidValueType(f"tags key '{key}'", key, "str")
            if not isinstance(value, (str, bool, float, int)):
                raise InvalidValueType(
                    f"tags value for key '{key}'", value, "str, bool, float, or int"
                )

    def _validate_timestamp(self, prediction_timestamp: Optional[int]) -> None:
        """Validate prediction timestamp"""
        if prediction_timestamp is None:
            return

        if not isinstance(prediction_timestamp, int):
            raise InvalidValueType("prediction_timestamp", prediction_timestamp, "int")

        current_time = int(time.time())
        if prediction_timestamp > current_time:
            logger.warning(
                "Caution: Sending a prediction with future timestamp. "
                "Fi only stores 2 years worth of data. Older data may be dropped."
            )

        if not is_timestamp_in_range(current_time, prediction_timestamp):
            raise ValueError(
                f"prediction_timestamp: {prediction_timestamp} is out of range. "
                f"Must be within {MAX_FUTURE_YEARS_FROM_CURRENT_TIME} year in the future and "
                f"{MAX_PAST_YEARS_FROM_CURRENT_TIME} years in the past from current time."
            )

    def _validate_chat_history(self, chat_history: List[Dict[str, str]]) -> None:
        """Validate chat history structure and content"""
        if not isinstance(chat_history, list):
            raise InvalidValueType("conversation['chat_history']", chat_history, "list")

        for item in chat_history:
            if not isinstance(item, dict):
                raise InvalidValueType("chat_history item", item, "dict")

            required_keys = ["role", "content"]
            for key in required_keys:
                if key not in item:
                    raise MissingRequiredKey("chat_history item", key)

            if not isinstance(item["role"], str):
                raise InvalidValueType("chat_history role", item["role"], "str")
            if not isinstance(item["content"], str):
                raise InvalidValueType("chat_history content", item["content"], "str")

    def _validate_chat_graph(self, chat_graph: Dict) -> None:
        """Validate chat graph structure and content"""
        required_keys = ["conversation_id", "nodes"]
        for key in required_keys:
            if key not in chat_graph:
                raise MissingRequiredKey("chat_graph", key)

        if not isinstance(chat_graph["nodes"], list):
            raise InvalidValueType("chat_graph['nodes']", chat_graph["nodes"], "list")

        for node in chat_graph["nodes"]:
            if "message" not in node:
                raise MissingRequiredKey("chat_graph node", "message")

            message = node["message"]
            if not isinstance(message, dict):
                raise InvalidValueType("node message", message, "dict")

            message_required_keys = ["id", "author", "content", "context"]
            for key in message_required_keys:
                if key not in message:
                    raise MissingRequiredKey("message", key)

            author = message["author"]
            author_required_keys = ["role", "metadata"]
            for key in author_required_keys:
                if key not in author:
                    raise MissingRequiredKey("author", key)

            if author["role"] not in ["assistant", "user", "system"]:
                raise InvalidValueType(
                    "author role", author["role"], "one of: assistant, user, system"
                )

            content = message["content"]
            content_required_keys = ["content_type", "parts"]
            for key in content_required_keys:
                if key not in content:
                    raise MissingRequiredKey("content", key)

            if not isinstance(content["parts"], list):
                raise InvalidValueType("content parts", content["parts"], "list")

    def log(
        self,
        model_id: str,
        model_type: ModelTypes,
        environment: Environments,
        model_version: Optional[str] = None,
        prediction_timestamp: Optional[int] = None,
        conversation: Optional[Dict[str, Union[str, bool, float, int]]] = None,
        tags: Optional[Dict[str, Union[str, bool, float, int]]] = None,
        timeout: Optional[int] = None,
    ) -> Response:
        """Unsupported on the current platform; retained for source compatibility.

        The Future AGI platform removed ``POST /sdk/api/v1/log/model/`` before
        version 1.56.1. No replacement accepts its model-log payload.
        Use traceAI instrumentation to emit traces and
        ``client.tracing`` on a ``FutureAGIClient`` to query stored traces; neither
        is a drop-in model-log replacement. Raises
        ``fi.errors.PlatformNotConfiguredError`` locally, before validating a
        payload or making any HTTP request.
        """
        raise PlatformNotConfiguredError(
            "Client.log is unsupported on the current platform: "
            "POST /sdk/api/v1/log/model/ was removed before Future AGI platform 1.56.1; "
            "there is no replacement accepting the legacy model-log payload. "
            "Use traceAI instrumentation (https://github.com/future-agi/traceAI) to emit traces "
            "and client.tracing on a FutureAGIClient to query stored traces; "
            "these are not drop-in model-log replacements.",
            code="unsupported_operation",
            operation="Client.log",
        )
