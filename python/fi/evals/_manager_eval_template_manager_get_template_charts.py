"""EvalTemplateManager get template charts operations."""
from __future__ import annotations

from fi.evals.manager import (
    Any, Dict, List, Optional, PlaygroundRunResponse, TemplateChartsResponse,
    TemplateDuplicateResponse,
)


class _EvalTemplateManagerGetTemplateChartsMethods:
    __slots__ = ()

    def get_template_charts(
        self, template_ids: List[str]
    ) -> TemplateChartsResponse:
        """
        30-day sparkline data (run counts + error rates) for the given
        templates — the same payload that powers the eval-list table.
        """
        from fi.evals.manager import (
            HttpMethod, List, RequestConfig, Routes, TemplateChartsResponse, _JsonResponseHandler,
        )
        url = f"{self._base_url}/{Routes.eval_template_list_charts.value}"
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=url,
                json={"template_ids": list(template_ids)},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateChartsResponse.model_validate(raw)


    def duplicate_template(
        self, template_id: str, name: str
    ) -> TemplateDuplicateResponse:
        """
        Clone an existing user-owned eval template under a new ``name``.
        Returns ``{message, eval_template_id}``.
        """
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, TemplateDuplicateResponse, _JsonResponseHandler,
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_template_duplicate.value}",
                json={"eval_template_id": template_id, "name": name},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateDuplicateResponse.model_validate(raw)


    def run_playground(
        self,
        template_id: str,
        *,
        mapping: Dict[str, Any],
        model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        input_data_types: Optional[Dict[str, str]] = None,
        error_localizer: bool = False,
        kb_id: Optional[str] = None,
        # Auto-context: pass either a resolved dict, or let the server
        # resolve via the matching id.
        row_context: Optional[Dict[str, Any]] = None,
        span_context: Optional[Dict[str, Any]] = None,
        trace_context: Optional[Dict[str, Any]] = None,
        session_context: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,
        span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        call_id: Optional[str] = None,
    ) -> PlaygroundRunResponse:
        """
        Run a saved eval template via the playground endpoint.

        Unlike :py:meth:`fi.evals.Evaluator.evaluate` — which identifies
        the eval by name — this identifies by ``template_id`` and
        exercises the full runtime config path, including auto-context
        injection (row / span / trace / session / call). Useful for
        test-drive workflows that want to run a specific template
        version against a specific trace or dataset row.

        Selecting Turing/Protect models requires an Enterprise licence including
        those models on self-hosted servers; cloud plan checks are separate.
        A model-gate denial returns HTTP 402 ENTITLEMENT_DENIED and retains this
        legacy client's Exception contract, not LicenseRequiredError. Select
        another model or ask the server administrator to enable the licensed
        models. Code evaluations are exempt from this model gate.
        """
        from fi.evals.manager import (
            Any, Dict, HttpMethod, Optional, PlaygroundRunResponse, RequestConfig, Routes,
            _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "template_id": template_id,
            "mapping": mapping,
            "error_localizer": error_localizer,
        }
        if model is not None:
            payload["model"] = model
        if config is not None:
            payload["config"] = config
        if input_data_types is not None:
            payload["input_data_types"] = input_data_types
        if kb_id is not None:
            payload["kb_id"] = kb_id
        for key, value in (
            ("row_context", row_context),
            ("span_context", span_context),
            ("trace_context", trace_context),
            ("session_context", session_context),
            ("call_context", call_context),
            ("span_id", span_id),
            ("trace_id", trace_id),
            ("session_id", session_id),
            ("call_id", call_id),
        ):
            if value is not None:
                payload[key] = value

        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_playground.value}",
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return PlaygroundRunResponse.model_validate(raw)
