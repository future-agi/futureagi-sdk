"""EvalTemplateManager typed request operations."""
from __future__ import annotations

from fi.evals.manager import (
    Any, BulkDeleteResponse, Dict, List, Literal, Optional, RequestConfig, TemplateCreateResponse,
    TemplateDetailResponse, TemplateListResponse, TemplateUpdateResponse, VersionCreateResponse,
    VersionListResponse, VersionSetDefaultResponse,
)


class _EvalTemplateManagerTypedRequestMethods:
    __slots__ = ()

    def _typed_request(self, config: RequestConfig, response_type: Any = None) -> Any:
        """Make a request and parse the response into a typed model."""
        from fi.evals.manager import (Any, RequestConfig, _JsonResponseHandler)
        raw = self.request(config=config, response_handler=_JsonResponseHandler)
        if response_type is None or isinstance(raw, str):
            return raw
        return response_type.model_validate(raw)


    def list_templates(
        self,
        *,
        page: int = 0,
        page_size: int = 25,
        search: Optional[str] = None,
        owner_filter: Literal["all", "user", "system"] = "all",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Literal["name", "updated_at", "created_at"] = "updated_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> TemplateListResponse:
        """List eval templates with pagination, search, and filters.

        Returns a dict with ``items``, ``total``, ``page``, ``page_size``.
        """
        from fi.evals.manager import (
            Any, Dict, HttpMethod, Literal, Optional, RequestConfig, Routes, TemplateListResponse,
            _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "owner_filter": owner_filter,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if search is not None:
            payload["search"] = search
        if filters is not None:
            payload["filters"] = filters

        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_template_list.value}",
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateListResponse.model_validate(raw)


    def get_template(self, template_id: str) -> TemplateDetailResponse:
        """Fetch a single eval template by UUID."""
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, TemplateDetailResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_detail.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateDetailResponse.model_validate(raw)


    def create_template(
        self,
        *,
        name: str,
        instructions: str = "",
        eval_type: Literal["llm", "code", "agent"] = "llm",
        model: str = "turing_large",
        output_type: Literal["pass_fail", "percentage", "deterministic"] = "pass_fail",
        pass_threshold: float = 0.5,
        choice_scores: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        check_internet: bool = False,
        code: Optional[str] = None,
        code_language: Optional[Literal["python", "javascript"]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        few_shot_examples: Optional[List[Dict[str, Any]]] = None,
        mode: Optional[Literal["auto", "agent", "quick"]] = None,
        tools: Optional[Dict[str, Any]] = None,
        knowledge_bases: Optional[List[str]] = None,
        data_injection: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None,
        is_draft: bool = False,
    ) -> TemplateCreateResponse:
        """
        Create a single eval template.

        The ``name`` must match ``[a-z0-9_-]+`` and cannot start/end with a
        separator (backend constraint). For ``eval_type="code"`` supply
        ``code``; otherwise supply ``instructions`` that reference at least
        one ``{{variable}}`` unless ``data_injection`` is enabled.
        """
        from fi.evals.manager import (
            Any, Dict, HttpMethod, List, Literal, Optional, RequestConfig, Routes,
            TemplateCreateResponse, _JsonResponseHandler,
        )
        payload: Dict[str, Any] = {
            "name": name,
            "is_draft": is_draft,
            "eval_type": eval_type,
            "instructions": instructions,
            "model": model,
            "output_type": output_type,
            "pass_threshold": pass_threshold,
            "tags": list(tags or []),
            "check_internet": check_internet,
        }
        if choice_scores is not None:
            payload["choice_scores"] = choice_scores
        if description is not None:
            payload["description"] = description
        if code is not None:
            payload["code"] = code
        if code_language is not None:
            payload["code_language"] = code_language
        if messages is not None:
            payload["messages"] = messages
        if few_shot_examples is not None:
            payload["few_shot_examples"] = few_shot_examples
        if mode is not None:
            payload["mode"] = mode
        if tools is not None:
            payload["tools"] = tools
        if knowledge_bases is not None:
            payload["knowledge_bases"] = knowledge_bases
        if data_injection is not None:
            payload["data_injection"] = data_injection
        if summary is not None:
            payload["summary"] = summary

        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_template_create_v2.value}",
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateCreateResponse.model_validate(raw)


    def update_template(
        self, template_id: str, **fields: Any
    ) -> TemplateUpdateResponse:
        """
        Update mutable fields on an eval template (PUT).

        Accepts any subset of: ``name``, ``eval_type``, ``instructions``,
        ``model``, ``output_type``, ``pass_threshold``, ``choice_scores``,
        ``multi_choice``, ``description``, ``tags``, ``check_internet``,
        ``code``, ``code_language``, ``messages``, ``few_shot_examples``,
        ``mode``, ``tools``, ``knowledge_bases``, ``data_injection``,
        ``summary``, ``error_localizer_enabled``, ``publish``.
        """
        from fi.evals.manager import (
            Any, HttpMethod, RequestConfig, Routes, TemplateUpdateResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_update_v2.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.PUT,
                url=url,
                json={k: v for k, v in fields.items() if v is not None},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateUpdateResponse.model_validate(raw)


    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Soft-delete an eval template."""
        from fi.evals.manager import (
            Any, Dict, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        return self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_template_delete.value}",
                json={"eval_template_id": template_id},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )


    def bulk_delete_templates(self, template_ids: List[str]) -> BulkDeleteResponse:
        """Soft-delete multiple eval templates in one call."""
        from fi.evals.manager import (
            BulkDeleteResponse, HttpMethod, List, RequestConfig, Routes, _JsonResponseHandler,
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.eval_template_bulk_delete.value}",
                json={"template_ids": list(template_ids)},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return BulkDeleteResponse.model_validate(raw)


    def list_versions(self, template_id: str) -> VersionListResponse:
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, VersionListResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_version_list.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return VersionListResponse.model_validate(raw)


    def create_version(
        self,
        template_id: str,
        *,
        criteria: Optional[str] = None,
        model: Optional[str] = None,
        config_snapshot: Optional[Dict[str, Any]] = None,
    ) -> VersionCreateResponse:
        """
        Snapshot the current template state as a new version. Each param is
        optional — any value left ``None`` is copied from the live template.
        """
        from fi.evals.manager import (
            Any, Dict, HttpMethod, Optional, RequestConfig, Routes, VersionCreateResponse,
            _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_version_create.value.format(template_id=template_id)
        )
        payload: Dict[str, Any] = {}
        if criteria is not None:
            payload["criteria"] = criteria
        if model is not None:
            payload["model"] = model
        if config_snapshot is not None:
            payload["config_snapshot"] = config_snapshot

        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=url,
                json=payload,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return VersionCreateResponse.model_validate(raw)


    def set_default_version(
        self, template_id: str, version_id: str
    ) -> VersionSetDefaultResponse:
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, VersionSetDefaultResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_version_set_default.value.format(
                template_id=template_id, version_id=version_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.PUT, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return VersionSetDefaultResponse.model_validate(raw)
