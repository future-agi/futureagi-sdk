"""
Management client for the revamped eval template API.

Covers the `/model-hub/eval-templates/*` surface introduced in the backend
Evals Revamp (Phases 1–7): list, create, detail, update, delete, versions,
and composite evals. For execution of single evals use
``fi.evals.Evaluator.evaluate``; this client is for managing the templates
themselves.
"""

import logging
import threading
import uuid
from typing import Any, Dict, List, Literal, Optional, Union

from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.evals.execution import Execution
from fi.evals.manager_types import (
    BulkDeleteResponse,
    CompositeCreateResponse,
    CompositeDetailResponse,
    CompositeExecutionResponse,
    GroundTruthConfigResponse,
    GroundTruthDataResponse,
    GroundTruthDeleteResponse,
    GroundTruthListResponse,
    GroundTruthRoleMappingResponse,
    GroundTruthSearchResponse,
    GroundTruthStatusResponse,
    GroundTruthUploadResponse,
    GroundTruthVariableMappingResponse,
    PlaygroundRunResponse,
    TemplateChartsResponse,
    TemplateCreateResponse,
    TemplateDetailResponse,
    TemplateDuplicateResponse,
    TemplateFeedbackListResponse,
    TemplateListResponse,
    TemplateUpdateResponse,
    TemplateUsageResponse,
    VersionCreateResponse,
    VersionListResponse,
    VersionRestoreResponse,
    VersionSetDefaultResponse,
)
from fi.utils.errors import InvalidAuthError
from fi.utils.routes import Routes


logger = logging.getLogger(__name__)


class _JsonResponseHandler(ResponseHandler[Dict[str, Any], None]):
    """Return the ``result`` payload from a standard backend response."""

    @classmethod
    def _parse_success(cls, response: Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            raise Exception(f"Non-JSON response: {response.text}")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        if response.status_code == 404:
            raise Exception(f"Not found: {response.text}")
        raise Exception(
            f"Eval template API error {response.status_code}: {response.text}"
        )


from ._manager_eval_template_manager_typed_request import _EvalTemplateManagerTypedRequestMethods
from ._manager_eval_template_manager_restore_version import _EvalTemplateManagerRestoreVersionMethods
from ._manager_eval_template_manager_get_ground_truth_config import _EvalTemplateManagerGetGroundTruthConfigMethods
from ._manager_eval_template_manager_get_template_charts import _EvalTemplateManagerGetTemplateChartsMethods

class EvalTemplateManager(
    _EvalTemplateManagerTypedRequestMethods,
    _EvalTemplateManagerRestoreVersionMethods,
    _EvalTemplateManagerGetGroundTruthConfigMethods,
    _EvalTemplateManagerGetTemplateChartsMethods,
    APIKeyAuth,
):
    """
    Client for managing eval templates on Future AGI.

    Example::

        from fi.evals import EvalTemplateManager

        mgr = EvalTemplateManager()
        t = mgr.create_template(
            name="is-polite",
            eval_type="llm",
            instructions="Is the {{output}} polite? Answer yes or no.",
            output_type="pass_fail",
            pass_threshold=0.7,
        )
        print(t.id)           # attribute access (autocomplete ✓)
        print(t["id"])         # dict access (backwards compat ✓)
        mgr.delete_template(t.id)
    """
