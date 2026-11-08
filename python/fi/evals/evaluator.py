import inspect
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler


def _coerce_to_api_input(value: Any) -> Any:
    """The api accepts strings, list[str], or list[list[str]]. Serialize
    anything richer (dict, list[dict], list[mixed]) to JSON so users can
    pass native Python objects for conversation/messages/structured inputs.
    """
    if isinstance(value, dict):
        return json.dumps(value)
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return value
        if all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in value):
            return value
        return json.dumps(value)
    return value
from fi.api.types import HttpMethod, RequestConfig
from fi.evals.execution import Execution, _normalize_status
from fi.evals.templates import EvalTemplate
from fi.evals.types import BatchRunResult, EvalResult
from fi.utils.errors import InvalidAuthError
from fi.utils.routes import Routes

try:
    from opentelemetry import trace
    from opentelemetry import trace as otel_trace_api
except ImportError:
    pass


from ._evaluator_eval_response_handler_parse_success import _EvalResponseHandlerParseSuccessMethods

class EvalResponseHandler(
    _EvalResponseHandlerParseSuccessMethods,
    ResponseHandler[BatchRunResult,
    None],
):
    """Handles responses for evaluation requests"""


class EvalInfoResponseHandler(ResponseHandler[dict, None]):
    """Handles responses for evaluation info requests"""

    @classmethod
    def _parse_success(cls, response: Response) -> dict:
        data = response.json()
        if "result" in data:
            return data["result"]
        else:
            raise Exception(f"Failed to get evaluation info: {data}")

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 400:
            response.raise_for_status()
        if response.status_code == 403:
            raise InvalidAuthError()
        raise Exception(f"Failed to get evaluation info: {response.status_code}")


from ._evaluator_evaluator_evaluate import _EvaluatorEvaluateMethods
from ._evaluator_evaluator_submit import _EvaluatorSubmitMethods
from ._evaluator_evaluator_evaluate_pipeline import _EvaluatorEvaluatePipelineMethods

class Evaluator(
    _EvaluatorEvaluateMethods,
    _EvaluatorSubmitMethods,
    _EvaluatorEvaluatePipelineMethods,
    APIKeyAuth,
):
    """Client for evaluating LLM test cases"""

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Eval Client

        Args:
            fi_api_key: API key
            fi_secret_key: Secret key
            fi_base_url: Base URL

        Keyword Args:
            timeout: Optional timeout value in seconds (default: 200)
            max_queue_bound: Optional maximum queue size (default: 5000)
            max_workers: Optional maximum number of workers (default: 8)
            langfuse_secret_key: Optional Langfuse secret key
            langfuse_public_key: Optional Langfuse public key
            langfuse_host: Optional Langfuse host
        """
        super().__init__(fi_api_key, fi_secret_key, fi_base_url, **kwargs)
        self._max_workers = kwargs.get("max_workers", 8)  # Default to 8 if not provided

        # Handle Langfuse credentials
        self.langfuse_secret_key = kwargs.get("langfuse_secret_key") or os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_public_key = kwargs.get("langfuse_public_key") or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_host = kwargs.get("langfuse_host") or os.getenv("LANGFUSE_HOST")


# Top-level convenience for the common "list everything" case.
# The main ``evaluate()`` entrypoint is imported from ``fi.evals.core``.
list_evaluations = lambda: Evaluator().list_evaluations()
