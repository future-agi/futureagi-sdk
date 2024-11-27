import concurrent.futures as cf
import time
from typing import Dict, Optional, Union

from requests_futures.sessions import FuturesSession

from fi.api.auth import APIKeyAuth
from fi.api.types import RequestType
from fi.bounded_executor import BoundedExecutor
from fi.utils.constants import (
    MAX_FUTURE_YEARS_FROM_CURRENT_TIME,
    MAX_PAST_YEARS_FROM_CURRENT_TIME,
)
from fi.utils.errors import (
    InvalidAdditionalHeaders,
    InvalidSupportedType,
    InvalidValueType,
    MissingRequiredKey,
)
from fi.utils.logging import logger
from fi.utils.types import Environments, ModelTypes
from fi.utils.utils import is_timestamp_in_range


class Client(APIKeyAuth):
    def __init__(
        self,
        fi_api_key: str = None,
        fi_secret_key: str = None,
        url: str = None,
        max_workers: int = 8,
        max_queue_bound: int = 5000,
        timeout: int = 200,
        additional_headers: Dict[str, str] = None,
    ) -> None:
        """
        Initializes the Fi Client
        :param fi_api_key: provided API key associated with your account.
        :param fi_secret_key: provided SECRET key associated with your account.
        :param max_workers: maximum number of concurrent requests to fi. Defaults
                to 8.
        :param max_queue_bound: maximum number of concurrent future objects
                generated for publishing to fi. Defaults to 5000.
        :param timeout: how long to wait for the server to send data before giving
                up. Defaults to 200.
        :param additional_headers: Dictionary of additional headers to
                append to request
        """
        super().__init__(fi_api_key, fi_secret_key, url)

        self._timeout = timeout
        self._session = FuturesSession(
            executor=BoundedExecutor(max_queue_bound, max_workers)
        )

        if additional_headers is not None:
            conflicting_keys = self.headers.keys() & additional_headers.keys()
            if conflicting_keys:
                raise InvalidAdditionalHeaders(conflicting_keys)
            self.headers.update(additional_headers)

    @property
    def session(self):
        return self._session

    @property
    def headers(self) -> dict:
        return {
            "X-Api-Key": self._fi_api_key,
            "X-Secret-Key": self._fi_secret_key,
        }

    @property
    def url(self) -> str:
        return f"{self.BASE_URL}/sdk/api/v1/log/model/"

    @property
    def params(self) -> dict:
        if not hasattr(self, "_params"):
            self._params = {}
        return self._params

    @property
    def payload(self) -> dict:
        if not hasattr(self, "_payload"):
            self._payload = {}
        return self._payload

    def _now(self):
        return time.time()

    def __validate_params(
        self,
        model_id: str,
        model_type: ModelTypes,
        environment: Environments,
        model_version: Optional[str] = None,
        prediction_timestamp: Optional[int] = None,
        conversation: Optional[Dict[str, Union[str, bool, float, int]]] = None,
        tags: Optional[Dict[str, Union[str, bool, float, int]]] = None,
    ):
        """
        Validates input parameters against specified standards.
        :param model_id:
        :param model_type:
        :param environment:
        :param model_version:
        :param prediction_timestamp:
        :param conversation:
        :param tags:
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
        if model_version:
            if not isinstance(model_version, str):
                raise InvalidValueType("model_version", model_version, "str")

        # Validate feature types
        if conversation:
            if isinstance(conversation, dict):
                if (
                    "chat_history" not in conversation
                    and "chat_graph" not in conversation
                ):
                    raise MissingRequiredKey(
                        "conversation", "[chat_history, chat_graph]"
                    )

                if "chat_history" in conversation:
                    chat_history = conversation["chat_history"]
                    if not isinstance(chat_history, list):
                        raise InvalidValueType(
                            "conversation['chat_history']", chat_history, "list"
                        )

                    for item in chat_history:
                        if not isinstance(item, dict):
                            raise InvalidValueType(
                                "conversation['chat_history'] item", item, "dict"
                            )

                        required_keys = ["role", "content"]
                        for key in required_keys:
                            if key not in item:
                                raise MissingRequiredKey(
                                    "conversation['chat_history'] item", key
                                )

                        if not isinstance(item["role"], str):
                            raise InvalidValueType(
                                "conversation['chat_history']['role']",
                                item["role"],
                                "str",
                            )

                if "chat_graph" in conversation:
                    feature = conversation["chat_graph"]
                    required_keys = ["conversation_id", "nodes"]
                    # required_keys = ["conversation_id", "title", "root_node", "metadata", "nodes"]
                    for key in required_keys:
                        if key not in feature:
                            raise MissingRequiredKey("conversation item", key)

                    if not isinstance(feature["nodes"], list):
                        raise InvalidValueType(
                            "conversation['nodes']", feature["nodes"], "list"
                        )

                    for node in feature["nodes"]:
                        node_required_keys = ["message"]
                        # node_required_keys = ["parent_node", "child_node", "message"]
                        for key in node_required_keys:
                            if key not in node:
                                raise MissingRequiredKey(
                                    "conversation['nodes'] item", key
                                )

                        if not isinstance(node["message"], dict):
                            raise InvalidValueType(
                                "conversation['nodes']['message']",
                                node["message"],
                                "dict",
                            )

                        message_required_keys = ["id", "author", "content", "context"]
                        for key in message_required_keys:
                            if key not in node["message"]:
                                raise MissingRequiredKey(
                                    "conversation['nodes']['message']", key
                                )

                        author_required_keys = ["role", "metadata"]
                        for key in author_required_keys:
                            if key not in node["message"]["author"]:
                                raise MissingRequiredKey(
                                    "conversation['nodes']['message']['author']", key
                                )

                        if node["message"]["author"]["role"] not in [
                            "assistant",
                            "user",
                            "system",
                        ]:
                            raise InvalidValueType(
                                "conversation['nodes']['message']['author']['role']",
                                node["message"]["author"]["role"],
                                "str",
                            )

                        content_required_keys = ["content_type", "parts"]
                        for key in content_required_keys:
                            if key not in node["message"]["content"]:
                                raise MissingRequiredKey(
                                    "conversation['nodes']['message']['content']", key
                                )

                        if not isinstance(node["message"]["content"]["parts"], list):
                            raise InvalidValueType(
                                "conversation['nodes']['message']['content']['parts']",
                                node["message"]["content"]["parts"],
                                "list",
                            )
            else:
                raise InvalidValueType("conversation", conversation, "dict or list")

        # Validate tags type
        if tags:
            if not isinstance(tags, dict):
                raise InvalidValueType("tags", tags, "dict")
            for key, value in tags.items():
                if not isinstance(key, str):
                    raise InvalidValueType("tags key", key, "str")

        # Check the timestamp present on the event
        if prediction_timestamp is not None:
            if not isinstance(prediction_timestamp, int):
                raise InvalidValueType(
                    "prediction_timestamp", prediction_timestamp, "int"
                )
            # Send warning if prediction is sent with future timestamp
            now = int(time.time())
            if prediction_timestamp > now:
                logger.warning(
                    "Caution when sending a prediction with future timestamp."
                    "fi only stores 2 years worth of data. For example, if you sent a prediction "
                    "to fi from 1.5 years ago, and now send a prediction with timestamp of a year in "
                    "the future, the oldest 0.5 years will be dropped to maintain the 2 years worth of data "
                    "requirement."
                )
            if not is_timestamp_in_range(now, prediction_timestamp):
                raise ValueError(
                    f"prediction_timestamp: {prediction_timestamp} is out of range."
                    f"Prediction timestamps must be within {MAX_FUTURE_YEARS_FROM_CURRENT_TIME} year in the "
                    f"future and {MAX_PAST_YEARS_FROM_CURRENT_TIME} years in the past from the current time."
                )

    def log(
        self,
        model_id: str,
        model_type: ModelTypes,
        environment: Environments,
        model_version: Optional[str] = None,
        prediction_timestamp: Optional[int] = None,
        conversation: Optional[Dict[str, Union[str, bool, float, int]]] = None,
        tags: Optional[Dict[str, Union[str, bool, float, int]]] = None,
    ) -> cf.Future:
        """
        Check `readme.md` for details on these parameters.

        :param model_id:
        :param model_type:
        :param environment:
        :param model_version:
        :param prediction_timestamp:
        :param conversation:
        :param tags:
        :return:
        """
        self.__validate_params(
            model_id=model_id,
            model_type=model_type,
            environment=environment,
            model_version=model_version,
            prediction_timestamp=prediction_timestamp,
            conversation=conversation,
            tags=tags,
        )

        self.payload.update(
            {
                "model_id": model_id,
                "model_type": model_type.value,
                "environment": environment.value,
                "model_version": model_version,
                "prediction_timestamp": prediction_timestamp,
                "conversation": conversation,
                "tags": tags,
            }
        )

        return self.make_request(
            request_type=RequestType.POST.value,
            payload=self.payload,
            url=self.url,
            params=self.params,
            headers=self.headers,
        )
