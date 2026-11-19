"""EvalTemplateManager restore version operations."""
from __future__ import annotations

from fi.evals.manager import (
    Any, CompositeCreateResponse, CompositeDetailResponse, CompositeExecutionResponse, Dict,
    Execution, GroundTruthListResponse, GroundTruthUploadResponse, List, Literal, Optional,
    VersionRestoreResponse,
)


class _EvalTemplateManagerRestoreVersionMethods:
    __slots__ = ()

    def restore_version(
        self, template_id: str, version_id: str
    ) -> VersionRestoreResponse:
        """
        Create a new version on top of the template whose contents match
        the target version. The old version is left untouched.
        """
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, VersionRestoreResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_version_restore.value.format(
                template_id=template_id, version_id=version_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return VersionRestoreResponse.model_validate(raw)


    def create_composite(
        self,
        *,
        name: str,
        child_template_ids: List[str],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        aggregation_enabled: bool = True,
        aggregation_function: Literal[
            "weighted_avg", "avg", "min", "max", "pass_rate"
        ] = "weighted_avg",
        child_weights: Optional[Dict[str, float]] = None,
        composite_child_axis: Literal[
            "", "pass_fail", "percentage", "choices", "code"
        ] = "",
    ) -> CompositeCreateResponse:
        """
        Create a composite eval from existing eval templates. ``child_weights``
        maps template_id → weight (default 1.0). Setting
        ``composite_child_axis`` enforces a homogeneity check — every child
        must match that output axis (e.g. all ``pass_fail``).
        """
        from fi.evals.manager import (
            CompositeCreateResponse, Dict, HttpMethod, List, Literal, Optional, RequestConfig,
            Routes, _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "name": name,
            "child_template_ids": list(child_template_ids),
            "aggregation_enabled": aggregation_enabled,
            "aggregation_function": aggregation_function,
            "composite_child_axis": composite_child_axis,
            "tags": list(tags or []),
        }
        if description is not None:
            payload["description"] = description
        if child_weights is not None:
            payload["child_weights"] = child_weights

        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.composite_eval_create.value}",
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return CompositeCreateResponse.model_validate(raw)


    def get_composite(self, template_id: str) -> CompositeDetailResponse:
        from fi.evals.manager import (
            CompositeDetailResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.composite_eval_detail.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return CompositeDetailResponse.model_validate(raw)


    def update_composite(
        self,
        template_id: str,
        **fields: Any,
    ) -> CompositeDetailResponse:
        """PATCH the composite. Same field names as ``create_composite``."""
        from fi.evals.manager import (
            Any, CompositeDetailResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.composite_eval_detail.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.PATCH,
                url=url,
                json={k: v for k, v in fields.items() if v is not None},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return CompositeDetailResponse.model_validate(raw)


    def submit_composite(
        self,
        template_id: str,
        *,
        mapping: Dict[str, Any],
        model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        error_localizer: bool = False,
        input_data_types: Optional[Dict[str, str]] = None,
        span_context: Optional[Dict[str, Any]] = None,
        trace_context: Optional[Dict[str, Any]] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Execution:
        """
        Submit a composite eval for non-blocking execution.

        The backend's composite execute endpoint is still synchronous,
        so this method offloads the HTTP call to a background thread
        inside the calling process and returns an :class:`Execution`
        handle immediately. Use ``handle.wait()`` to block until the
        run finishes, or poll ``handle.is_done()`` yourself.

        IMPORTANT: The execution ID is client-local — if this process
        dies or you drop the handle, the in-flight work is lost. For
        cross-process resumable runs, use
        :py:meth:`fi.evals.Evaluator.submit` against a single eval.
        """
        from fi.evals.manager import (Any, Dict, Execution, Optional, logger, threading, uuid)
        handle = Execution(
            id=str(uuid.uuid4()),
            kind="composite",
            status="pending",
        )
        # Keep a reference so the thread isn't GC'd while running.
        handle._refresher = lambda h=handle: h  # type: ignore[attr-defined]

        def _runner() -> None:
            handle.status = "processing"
            try:
                result = self.execute_composite(
                    template_id,
                    mapping=mapping,
                    model=model,
                    config=config,
                    error_localizer=error_localizer,
                    input_data_types=input_data_types,
                    span_context=span_context,
                    trace_context=trace_context,
                    session_context=session_context,
                )
                handle.result = result
                if isinstance(result, dict):
                    handle.error_localizer = result.get("error_localizer_results")
                handle.status = "completed"
            except Exception as exc:  # noqa: BLE001
                handle.error_message = f"{exc.__class__.__name__}: {exc}"
                handle.status = "failed"
                logger.exception(
                    "Composite execution %s failed: %s", handle.id, exc
                )

        thread = threading.Thread(
            target=_runner, daemon=True, name=f"fi-composite-{handle.id[:8]}"
        )
        thread.start()
        return handle


    def execute_composite(
        self,
        template_id: str,
        *,
        mapping: Dict[str, Any],
        model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        error_localizer: bool = False,
        input_data_types: Optional[Dict[str, str]] = None,
        span_context: Optional[Dict[str, Any]] = None,
        trace_context: Optional[Dict[str, Any]] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> CompositeExecutionResponse:
        """
        Run every child eval in the composite with a single input mapping
        and return per-child results plus the aggregated score.
        """
        from fi.evals.manager import (
            Any, CompositeExecutionResponse, Dict, HttpMethod, Optional, RequestConfig, Routes,
            _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "mapping": mapping,
            "config": config or {},
            "error_localizer": error_localizer,
            "input_data_types": input_data_types or {},
        }
        if model is not None:
            payload["model"] = model
        if span_context is not None:
            payload["span_context"] = span_context
        if trace_context is not None:
            payload["trace_context"] = trace_context
        if session_context is not None:
            payload["session_context"] = session_context

        url = (
            f"{self._base_url}/"
            + Routes.composite_eval_execute.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=url,
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return CompositeExecutionResponse.model_validate(raw)


    def list_ground_truth(self, template_id: str) -> GroundTruthListResponse:
        """List ground-truth datasets attached to an eval template."""
        from fi.evals.manager import (
            GroundTruthListResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_list.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return GroundTruthListResponse.model_validate(raw)


    def upload_ground_truth(
        self,
        template_id: str,
        *,
        name: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        description: str = "",
        file_name: str = "",
        variable_mapping: Optional[Dict[str, str]] = None,
        role_mapping: Optional[Dict[str, str]] = None,
    ) -> GroundTruthUploadResponse:
        """
        Upload a ground-truth dataset as a JSON body (``columns`` +
        ``data`` rows). For file-upload mode (CSV/XLSX) use the HTTP API
        directly — the SDK does not wrap multipart uploads yet.
        """
        from fi.evals.manager import (
            Any, Dict, GroundTruthUploadResponse, HttpMethod, List, Optional, RequestConfig,
            Routes, _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "name": name,
            "description": description,
            "file_name": file_name,
            "columns": list(columns),
            "data": list(data),
        }
        if variable_mapping is not None:
            payload["variable_mapping"] = variable_mapping
        if role_mapping is not None:
            payload["role_mapping"] = role_mapping

        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_upload.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=url,
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return GroundTruthUploadResponse.model_validate(raw)
