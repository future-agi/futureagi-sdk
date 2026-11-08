"""A lazily retained evaluator sharing the root client's resolved HTTP configuration."""
from __future__ import annotations

import threading
from typing import Any, Callable


class EvaluatorDelegate:
    """Own evaluators, but borrow the platform client's transport and connection pool.

    Replaced evaluators are retained until close because another thread may still be using them.
    Each with_options copy has its own delegate, so closing a copy cannot dispose its parent's
    evaluator. Closing a delegate is idempotent and never initializes an unused evaluator.
    """

    def __init__(self, credentials: Callable[[], Any], http_client: Callable[[], Any]) -> None:
        self._credentials = credentials
        self._http_client = http_client
        self._lock = threading.Lock()
        self._held: Any = None
        self._retired: list[Any] = []
        self._closed = False

    def evaluator(self) -> Any:
        creds = self._credentials()
        key = (creds.api_key or "", creds.secret_key or "", creds.base_url)
        with self._lock:
            if self._closed:
                raise RuntimeError("the evaluation client is closed")
            if self._held is None or self._held[0] != key:
                from fi.evals._client_transport import ClientEvaluator

                evaluator = ClientEvaluator(http_client=self._http_client, fi_api_key=key[0],
                                            fi_secret_key=key[1], fi_base_url=key[2])
                if self._held is not None:
                    self._retired.append(self._held[1])
                self._held = (key, evaluator)
            return self._held[1]

    def evaluate(self, eval_templates: Any, inputs: Any, **kwargs: Any) -> Any:
        return self.evaluator().evaluate(eval_templates, inputs, **kwargs)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            evaluators = self._retired + ([self._held[1]] if self._held is not None else [])
            self._held, self._retired = None, []
        for evaluator in evaluators:
            evaluator.close()
