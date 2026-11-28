"""Evaluator evaluate pipeline operations."""
from __future__ import annotations

from fi.evals.evaluator import (Any, Dict, List)


class _EvaluatorEvaluatePipelineMethods:
    __slots__ = ()

    def evaluate_pipeline(
            self,
            project_name: str,
            version : str,
            eval_data : List[Dict[str, Any]],
    ):
        from fi.evals.evaluator import (Any, Dict, HttpMethod, List, RequestConfig, Routes)
        api_payload = {
            "project_name": project_name,
            "version": version,
            "eval_data": eval_data
        }

        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.evaluate_pipeline.value}",
                json=api_payload,
                timeout=self._default_timeout,
            ),
        )

        return response.json()


    def get_pipeline_results(
            self,
            project_name: str,
            versions : List[str],
    ):

        from fi.evals.evaluator import (HttpMethod, List, RequestConfig, Routes)
        if not isinstance(versions, list) or not all(isinstance(v, str) for v in versions):
            raise TypeError("versions must be a list of strings")

        api_payload = {
            "project_name": project_name,
            "versions": ",".join(versions),
        }

        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=f"{self._base_url}/{Routes.evaluate_pipeline.value}",
                params=api_payload,
                timeout=self._default_timeout,
            ),
        )

        return response.json()
