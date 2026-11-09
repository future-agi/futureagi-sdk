"""Evaluator submit operations."""
from __future__ import annotations

from fi.evals.evaluator import (Any, Dict, EvalTemplate, Execution, Optional, Union, lru_cache)


class _EvaluatorSubmitMethods:
    __slots__ = ()

    def submit(
        self,
        eval_templates: Union[str, type[EvalTemplate]],
        inputs: Dict[str, Any],
        *,
        model_name: Optional[str] = None,
        custom_eval_name: Optional[str] = None,
        trace_eval: bool = False,
        error_localizer: bool = False,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> Execution:
        """
        Submit an eval for async execution and return an :class:`Execution`
        handle immediately. Use ``handle.wait()`` or
        :py:meth:`get_execution` to poll for completion.

        List-valued inputs require ``batch=True``. This returns a batch handle
        with every server ID in ``handle.ids`` and individually resumable handles
        in ``handle.executions``; ``wait()`` waits for all jobs and ``result`` is
        an ordered list. Without that opt-in, batch inputs are rejected before
        submission. Multiple IDs in any response are always retained together.

        This is the non-blocking equivalent of :py:meth:`evaluate` —
        internally it always sets ``is_async=True`` so the backend records
        the evaluation and starts a worker without holding the HTTP
        connection open.
        """
        from fi.evals.evaluator import (
            Any, Dict, EvalTemplate, Execution, HttpMethod, Optional, RequestConfig, Routes, Union,
            inspect,
        )

        def _extract_name(t: Any) -> Optional[str]:
            if isinstance(t, str):
                return t
            if isinstance(t, EvalTemplate):
                return t.eval_name
            if inspect.isclass(t) and issubclass(t, EvalTemplate):
                return t.eval_name
            return None

        batch = kwargs.get("batch") is True
        if not batch and isinstance(inputs, dict) and any(isinstance(value, list) for value in inputs.values()):
            raise ValueError("List-valued batch inputs require batch=True; otherwise submit single inputs")

        eval_name = _extract_name(
            eval_templates[0] if isinstance(eval_templates, list) else eval_templates
        )
        if eval_name is None:
            raise TypeError(
                "Unsupported eval_templates argument. "
                "Expect eval template class/obj or name str."
            )

        payload = {
            "eval_name": eval_name,
            "inputs": inputs,
            "model": model_name,
            "span_id": kwargs.get("span_id"),
            "custom_eval_name": custom_eval_name,
            "trace_eval": trace_eval,
            "is_async": True,
            "error_localizer": error_localizer,
        }

        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.evaluatev2.value}",
                json=payload,
                timeout=timeout or self._default_timeout,
            ),
        )
        body = response.json() if hasattr(response, "json") else {}

        # Backend responds with:
        #   {"status": true,  "result": [{"evaluations": [{name, output_type, eval_id}]}]}
        # on success, or
        #   {"status": false, "result": {...error dict...}}
        # on validation failure.
        if not body.get("status", True):
            raise RuntimeError(
                f"Async submit rejected by backend: {body.get('result')}"
            )

        results = body.get("result") or []
        if not isinstance(results, list) or not results:
            raise RuntimeError(
                f"Async submit did not return a result list (response: {body})"
            )
        evaluations = [evaluation for result in results for evaluation in (result.get("evaluations") or [])]
        if not evaluations or any(not evaluation.get("eval_id") for evaluation in evaluations):
            raise RuntimeError(
                f"Async submit did not return an eval_id for every evaluation (response: {body})"
            )

        handles = []
        for evaluation in evaluations:
            execution_id = str(evaluation["eval_id"])
            handle = Execution(id=execution_id, kind="eval", status="pending")
            handle._refresher = lambda eid=execution_id: self._refresh_eval_execution(eid)
            handles.append(handle)
        if batch or len(handles) > 1:
            from fi.evals.core._batch_execution import BatchExecution
            return BatchExecution(handles)
        return handles[0]


    def get_execution(self, execution_id: str) -> Execution:
        """
        Fetch the latest state of an async single-eval execution by ID.

        Returns an :class:`Execution` handle with an attached refresher
        closure — call ``handle.wait()`` to block until completion.
        """
        from fi.evals.evaluator import (Execution)
        handle = self._refresh_eval_execution(execution_id)
        handle._refresher = (
            lambda eid=execution_id: self._refresh_eval_execution(eid)
        )
        return handle


    def _refresh_eval_execution(self, execution_id: str) -> Execution:
        from fi.evals.evaluator import (
            EvalResult, Execution, HttpMethod, RequestConfig, Routes, _normalize_status,
        )
        url = f"{self._base_url}/{Routes.get_eval_result.value}"
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params={"eval_id": execution_id},
                timeout=self._default_timeout,
            ),
        )
        body = response.json() if hasattr(response, "json") else {}
        # Envelope: {"status": true, "result": {"eval_status": ..., "result": <body|str>}}
        payload = body.get("result") or {}
        status = _normalize_status(payload.get("eval_status"))
        raw_result = payload.get("result")
        error_message = payload.get("error_message")

        parsed_result: Any = None
        error_localizer: Optional[Dict[str, Any]] = None
        if isinstance(raw_result, dict):
            # Completed / failed state — full eval record.
            parsed_result = EvalResult(
                name=raw_result.get("name", ""),
                output=raw_result.get("output", raw_result.get("value")),
                reason=raw_result.get("reason"),
                runtime=raw_result.get("runtime", 0),
                output_type=raw_result.get("output_type"),
                eval_id=str(raw_result.get("eval_id", execution_id)),
                model=raw_result.get("model"),
                error_localizer_enabled=raw_result.get("error_localizer_enabled"),
                error_localizer=raw_result.get("error_localizer"),
            )
            error_localizer = raw_result.get("error_localizer")
            error_message = raw_result.get("error_message") or error_message
        # else: raw_result is a human-readable string like "Evaluation is
        # being processed." — leave parsed_result as None.

        return Execution(
            id=str(execution_id),
            kind="eval",
            status=status,
            result=parsed_result,
            error_message=error_message,
            error_localizer=error_localizer,
        )


    def _configure_evaluations(
        self,
        eval_templates: str,
        inputs: Dict[str, Any],
        platform: str,
        custom_eval_name: str,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure evaluations on a specified platform.

        This will not return any evaluation results, but rather a
        confirmation message from the backend.

        Args:
            eval_config: The evaluation configuration dictionary.
            platform: The platform to which the evaluations should be sent.
            timeout: Optional timeout for the API request.
            **kwargs: Additional configuration parameters to be sent with the request.

        Returns:
            A dictionary containing the backend's response message.
        """
        from fi.evals.evaluator import (
            Any, Dict, HttpMethod, Optional, RequestConfig, Routes, logging,
        )
        try:
            from fi.evals.otel_utils import _get_current_otel_span

            if platform == "langfuse":
                kwargs["langfuse_secret_key"] = self.langfuse_secret_key
                kwargs["langfuse_public_key"] = self.langfuse_public_key
                kwargs["langfuse_host"] = self.langfuse_host

            current_span = _get_current_otel_span()
            if current_span:
                span_context = current_span.get_span_context()
                if span_context.is_valid:
                    span_id = format(span_context.span_id, "016x")
                    trace_id = format(span_context.trace_id, "032x")
                    kwargs["span_id"] = span_id
                    kwargs["trace_id"] = trace_id

            # Check if span_id and trace_id are present in kwargs
            if "span_id" not in kwargs or "trace_id" not in kwargs:
                logging.warning(
                    "span_id and/or trace_id not found in kwargs ."
                    "Please run this function within a span context."
                )
                return

            api_payload = {
                "eval_config": {
                    "eval_templates": eval_templates,
                    "inputs": inputs,
                    "model_name": model_name
                },
                "custom_eval_name": custom_eval_name,
                "platform": platform,
                **kwargs,
            }

            response = self.request(
                config=RequestConfig(
                    method=HttpMethod.POST,
                    url=f"{self._base_url}/{Routes.configure_evaluations.value}",
                    json=api_payload,
                    timeout=self._default_timeout,
                ),
            )

            if response.status_code != 200:
                logging.warning(
                    "Received non-200 status code from backend: %s for evaluation %s",
                    response.status_code, eval_templates,
                )

            return response.json()

        except ImportError as exc:
            logging.error(
                "Future AGI SDK not found. "
                "Please install 'fi-instrumentation-otel' to use these evaluations. "
                "Evaluation: %s; error type: %s",
                eval_templates, type(exc).__name__,
            )
            return


    @lru_cache(maxsize=100)
    def _get_eval_info(self, eval_name: str) -> Dict[str, Any]:
        from fi.evals.evaluator import (
            Any, Dict, EvalInfoResponseHandler, HttpMethod, RequestConfig, Routes, lru_cache,
        )
        url = (
            self._base_url
            + "/"
            + Routes.get_eval_templates.value
        )
        response = self.request(
            config=RequestConfig(method=HttpMethod.GET, url=url),
            response_handler=EvalInfoResponseHandler,
        )
        eval_info = next((item for item in response if item["name"] == eval_name), None)
        if eval_info is None:
            raise KeyError(f"Evaluation template '{eval_name}' not found in registry")
        if not eval_info:
            raise Exception(f"Evaluation template with name '{eval_name}' not found")
        return eval_info


    def list_evaluations(self):
        """
        Fetch information about all available evaluation templates by getting eval_info
        for each template class defined in templates.py.

        Returns:
            List[Dict[str, Any]]: List of evaluation template information dictionaries
        """
        from fi.evals.evaluator import (EvalInfoResponseHandler, HttpMethod, RequestConfig, Routes)
        config = RequestConfig(method=HttpMethod.GET,
                                url=f"{self._base_url}/{Routes.get_eval_templates.value}")

        response = self.request(config=config, response_handler=EvalInfoResponseHandler)

        return response
