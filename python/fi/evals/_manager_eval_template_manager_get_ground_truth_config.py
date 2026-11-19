"""EvalTemplateManager get ground truth config operations."""
from __future__ import annotations

from fi.errors import ConfigurationValueError, PlatformNotConfiguredError
from fi.evals.manager import (
    Any, Dict, GroundTruthConfigResponse, GroundTruthDataResponse, GroundTruthDeleteResponse,
    GroundTruthRoleMappingResponse, GroundTruthSearchResponse, GroundTruthStatusResponse,
    GroundTruthVariableMappingResponse, Literal, Optional, TemplateFeedbackListResponse,
    TemplateUsageResponse,
)


class _EvalTemplateManagerGetGroundTruthConfigMethods:
    __slots__ = ()

    def get_ground_truth_config(self, template_id: str) -> GroundTruthConfigResponse:
        """Unsupported on the current platform; use :meth:`list_ground_truth`.

        Raises ``fi.errors.PlatformNotConfiguredError`` without making a request.
        The Future AGI platform removed the config endpoint before version 1.56.1.
        There is no compatible replacement: the list returns dataset state, without
        ``mode`` or ``injection_format``, not the legacy template config response.
        """
        raise PlatformNotConfiguredError(
            "get_ground_truth_config is unsupported on the current platform: "
            f"GET /model-hub/eval-templates/{template_id}/ground-truth-config/ "
            "was removed before Future AGI platform 1.56.1; no compatible replacement exists. "
            "Use list_ground_truth(template_id) via "
            f"GET /model-hub/eval-templates/{template_id}/ground-truth/ "
            "to read dataset state, not the legacy template config; "
            "mode and injection_format are unavailable.",
            code="unsupported_operation",
            operation="get_ground_truth_config",
        )


    def set_ground_truth_config(
        self,
        template_id: str,
        *,
        enabled: bool = True,
        ground_truth_id: Optional[str] = None,
        mode: Literal["auto", "manual", "disabled"] = "auto",
        max_examples: int = 3,
        similarity_threshold: float = 0.7,
        injection_format: Literal[
            "structured", "conversational", "xml"
        ] = "structured",
    ) -> GroundTruthConfigResponse:
        """Unsupported on the current platform; retained for source compatibility.

        Raises ``fi.errors.PlatformNotConfiguredError`` before HTTP. The Future AGI
        platform removed the config endpoint before version 1.56.1. The mapping
        setters support atomic setup by ground-truth ID, not template ID; setup
        cannot set ``mode``, ``similarity_threshold`` or ``injection_format`` and
        requires both mappings. It is not a compatible replacement for the legacy
        template config.
        """
        setup_id = ground_truth_id if ground_truth_id is not None else "{ground_truth_id}"
        raise PlatformNotConfiguredError(
            "set_ground_truth_config is unsupported on the current platform: "
            f"PUT /model-hub/eval-templates/{template_id}/ground-truth-config/ "
            "was removed before Future AGI platform 1.56.1; no compatible replacement exists. "
            "Use set_ground_truth_variable_mapping or set_ground_truth_role_mapping "
            "with a ground-truth ID, both mappings, max_examples and enabled via "
            f"PUT /model-hub/ground-truth/{setup_id}/setup/. "
            "Setup cannot set mode, similarity_threshold or injection_format.",
            code="unsupported_operation",
            operation="set_ground_truth_config",
        )


    def set_ground_truth_variable_mapping(
        self, ground_truth_id: str, variable_mapping: Dict[str, str], *,
        role_mapping: Optional[Dict[str, str]] = None,
        max_examples: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> GroundTruthVariableMappingResponse:
        """Map eval variables to GT columns using the atomic ``PUT .../setup/``.

        Breaking change: a two-argument call now raises before HTTP unless the
        complete ``role_mapping``, ``max_examples`` (1–20) and ``enabled`` are also
        passed as keywords. Read current state with ``list_ground_truth(template_id)``
        and preserve unchanged values; there is no setup read by GT ID or safe
        default. Missing or invalid setup state raises
        ``fi.errors.ConfigurationValueError`` (also a ``ValueError``).
        Role keys must be ``output``, ``explanation``, ``expected_output``,
        ``reasoning`` or ``reason``; unknown keys are rejected locally.

        Server side effects: setup makes this dataset the template's ACTIVE ground
        truth and deactivates the other datasets for the same template, organization
        and workspace, even when ``enabled=False``. Changing ``variable_mapping`` on
        a COMPLETED dataset resets ``embedding_status`` to PENDING; re-run
        ``trigger_ground_truth_embeddings(ground_truth_id)`` afterward.
        """
        from fi.evals.manager import GroundTruthVariableMappingResponse

        raw = self._set_ground_truth_setup(
            ground_truth_id, variable_mapping, role_mapping, max_examples, enabled
        )
        return GroundTruthVariableMappingResponse.model_validate(raw)


    def set_ground_truth_role_mapping(
        self, ground_truth_id: str, role_mapping: Dict[str, str], *,
        variable_mapping: Optional[Dict[str, str]] = None,
        max_examples: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> GroundTruthRoleMappingResponse:
        """Map ``output`` and optional ``explanation`` to GT columns via setup.

        Legacy role aliases are ``expected_output``, ``reasoning`` and ``reason``;
        all other role keys are rejected locally. Breaking change: a two-argument
        call now raises before HTTP unless the complete ``variable_mapping``,
        ``max_examples`` (1–20) and ``enabled`` are also passed as keywords. Read
        current state with ``list_ground_truth(template_id)`` and preserve unchanged
        values, rather than clearing the other mapping or re-enabling a disabled
        dataset. Missing or invalid setup state raises
        ``fi.errors.ConfigurationValueError`` (also a ``ValueError``).

        Server side effects: setup makes this dataset the template's ACTIVE ground
        truth and deactivates the other datasets for the same template, organization
        and workspace, even when ``enabled=False``. Changing ``variable_mapping`` on
        a COMPLETED dataset resets ``embedding_status`` to PENDING; re-run
        ``trigger_ground_truth_embeddings(ground_truth_id)`` afterward.
        """
        from fi.evals.manager import GroundTruthRoleMappingResponse

        raw = self._set_ground_truth_setup(
            ground_truth_id, variable_mapping, role_mapping, max_examples, enabled
        )
        return GroundTruthRoleMappingResponse.model_validate(raw)


    def _set_ground_truth_setup(
        self, ground_truth_id: str,
        variable_mapping: Optional[Dict[str, str]],
        role_mapping: Optional[Dict[str, str]],
        max_examples: Optional[int], enabled: Optional[bool],
    ) -> Dict[str, Any]:
        """Send the complete setup; never infer missing state from empty defaults."""
        from fi.evals.manager import HttpMethod, RequestConfig, Routes, _JsonResponseHandler

        payload = {
            "variable_mapping": variable_mapping,
            "role_mapping": role_mapping,
            "max_examples": max_examples,
            "enabled": enabled,
        }
        missing = [name for name, value in payload.items() if value is None]
        if missing:
            raise ConfigurationValueError(
                "Ground-truth setup requires complete state; required fields missing: "
                + ", ".join(missing)
                + ". Pass them explicitly (list_ground_truth(template_id) returns current state)."
            )
        if isinstance(max_examples, bool) or not isinstance(max_examples, int) or not 1 <= max_examples <= 20:
            raise ConfigurationValueError("max_examples must be an integer between 1 and 20 for ground-truth setup")
        if not isinstance(enabled, bool):
            raise ConfigurationValueError("enabled must be a boolean for ground-truth setup")
        # The platform's ground-truth setup serializer silently drops undeclared role keys.
        allowed_roles = {"output", "explanation", "expected_output", "reasoning", "reason"}
        unknown_roles = set(role_mapping) - allowed_roles
        if unknown_roles:
            raise ConfigurationValueError(
                "Unknown role_mapping keys: " + ", ".join(sorted(map(str, unknown_roles)))
                + ". Allowed keys: " + ", ".join(sorted(allowed_roles)) + "."
            )
        url = f"{self._base_url}/" + Routes.ground_truth_setup.value.format(ground_truth_id=ground_truth_id)
        return self.request(
            config=RequestConfig(
                method=HttpMethod.PUT, url=url, json=payload, timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )


    def get_ground_truth_data(
        self,
        ground_truth_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> GroundTruthDataResponse:
        """Paginated ground-truth rows (1-based page)."""
        from fi.evals.manager import (
            GroundTruthDataResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_data.value.format(
                ground_truth_id=ground_truth_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params={"page": page, "page_size": page_size},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return GroundTruthDataResponse.model_validate(raw)


    def get_ground_truth_status(self, ground_truth_id: str) -> GroundTruthStatusResponse:
        """Embedding generation status / progress for a ground-truth dataset."""
        from fi.evals.manager import (
            GroundTruthStatusResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_status.value.format(
                ground_truth_id=ground_truth_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )
        return GroundTruthStatusResponse.model_validate(raw)


    def trigger_ground_truth_embeddings(
        self, ground_truth_id: str
    ) -> Dict[str, Any]:
        """Kick off async embedding generation for a ground-truth dataset."""
        from fi.evals.manager import (
            Any, Dict, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_embed.value.format(
                ground_truth_id=ground_truth_id
            )
        )
        return self.request(
            config=RequestConfig(
                method=HttpMethod.POST, url=url, timeout=self._default_timeout
            ),
            response_handler=_JsonResponseHandler,
        )


    def search_ground_truth(
        self,
        ground_truth_id: str,
        *,
        query: str,
        max_results: int = 3,
    ) -> GroundTruthSearchResponse:
        """Unsupported on the current platform, with no replacement search route.

        Raises ``fi.errors.PlatformNotConfiguredError`` before HTTP, even if
        embeddings have completed. The Future AGI platform removed the search
        endpoint before version 1.56.1.
        :meth:`get_ground_truth_data` returns paginated rows, not similarity-search
        results, so it is not a compatible replacement. The signature is retained.
        """
        raise PlatformNotConfiguredError(
            "search_ground_truth is unsupported on the current platform: "
            f"POST /model-hub/ground-truth/{ground_truth_id}/search/ "
            "was removed before Future AGI platform 1.56.1; there is no replacement search route. "
            "Use get_ground_truth_data(ground_truth_id) via "
            f"GET /model-hub/ground-truth/{ground_truth_id}/data/ "
            "to read paginated rows, not similarity-search results.",
            code="unsupported_operation",
            operation="search_ground_truth",
        )


    def delete_ground_truth(self, ground_truth_id: str) -> GroundTruthDeleteResponse:
        """Soft-delete a ground-truth dataset."""
        from fi.evals.manager import (
            GroundTruthDeleteResponse, HttpMethod, RequestConfig, Routes, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.ground_truth_delete.value.format(
                ground_truth_id=ground_truth_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.DELETE,
                url=url,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return GroundTruthDeleteResponse.model_validate(raw)


    def get_template_usage(
        self,
        template_id: str,
        *,
        page: int = 0,
        page_size: int = 25,
        period: Literal["30m", "6h", "1d", "7d", "30d", "90d"] = "30d",
        version: Optional[str] = None,
    ) -> TemplateUsageResponse:
        """Paginated usage stats + run logs for an eval template."""
        from fi.evals.manager import (
            HttpMethod, Literal, Optional, RequestConfig, Routes, TemplateUsageResponse,
            _JsonResponseHandler,
        )
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "period": period,
        }
        if version is not None:
            params["version"] = version
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_usage.value.format(template_id=template_id)
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params=params,
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateUsageResponse.model_validate(raw)


    def list_template_feedback(
        self,
        template_id: str,
        *,
        page: int = 0,
        page_size: int = 25,
    ) -> TemplateFeedbackListResponse:
        """Paginated user feedback on an eval template's runs."""
        from fi.evals.manager import (
            HttpMethod, RequestConfig, Routes, TemplateFeedbackListResponse, _JsonResponseHandler,
        )
        url = (
            f"{self._base_url}/"
            + Routes.eval_template_feedback_list.value.format(
                template_id=template_id
            )
        )
        raw = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params={"page": page, "page_size": page_size},
                timeout=self._default_timeout,
            ),
            response_handler=_JsonResponseHandler,
        )
        return TemplateFeedbackListResponse.model_validate(raw)
