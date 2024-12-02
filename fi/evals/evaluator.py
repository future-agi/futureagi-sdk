from typing import Any, Dict, List, Optional, Union

from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.evals.templates import EvalTemplate
from fi.evals.types import BatchRunResult, EvalResult, EvalResultMetric
from fi.testcases import ConversationalTestCase, LLMTestCase, MLLMTestCase, TestCase
from fi.utils.routes import Routes


class EvalResponseHandler(ResponseHandler[BatchRunResult]):
    """Handles responses for evaluation requests"""

    @classmethod
    def _parse_success(cls, response: Response) -> BatchRunResult:
        return cls.convert_to_batch_results(response.json())

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 400:
            response.raise_for_status()

    @classmethod
    def convert_to_batch_results(cls, response: Dict[str, Any]) -> BatchRunResult:
        """
        Convert API response to BatchRunResult

        Args:
            response: Raw API response dictionary

        Returns:
            BatchRunResult containing evaluation results
        """
        eval_results = []

        for result in response.get("result", []):
            for evaluation in result.get("evaluations", []):
                eval_results.append(
                    EvalResult(
                        name=evaluation["name"],
                        display_name=evaluation["name"],
                        data=evaluation.get("data"),
                        failure=evaluation.get("failure"),
                        reason=evaluation.get("reason", ""),
                        runtime=evaluation.get("runtime", 0),
                        model=evaluation.get("model"),
                        metadata=evaluation.get("metadata"),
                        metrics=[
                            EvalResultMetric(id=metric["id"], value=metric["value"])
                            for metric in evaluation.get("metrics", [])
                        ],
                        datapoint_field_annotations=evaluation.get(
                            "datapointFieldAnnotations"
                        ),
                    )
                )

        return BatchRunResult(eval_results=eval_results)


class EvalClient(APIKeyAuth):
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
        """
        super().__init__(fi_api_key, fi_secret_key, fi_base_url, **kwargs)

    def evaluate(
        self,
        eval_templates: Union[EvalTemplate, List[EvalTemplate]],
        inputs: Union[
            TestCase,
            List[TestCase],
            LLMTestCase,
            List[LLMTestCase],
            MLLMTestCase,
            List[MLLMTestCase],
            ConversationalTestCase,
            List[ConversationalTestCase],
        ],
        timeout: Optional[int] = None,
    ) -> BatchRunResult:
        """
        Run a single or batch of evaluations independently

        Args:
            eval_templates: Single evaluation template or list of evaluation templates
            inputs: Single LLM test case or list of LLM test cases
            timeout: Optional timeout value for the evaluation

        Returns:
            BatchRunResult containing evaluation results

        Raises:
            ValidationError: If the inputs do not match the evaluation templates
            Exception: If the API request fails
        """
        # Convert single items to lists for consistent handling
        if not isinstance(eval_templates, list):
            eval_templates = [eval_templates]
        if not isinstance(inputs, list):
            inputs = [inputs]

        # Validate inputs
        self._validate_inputs(inputs, eval_templates)

        # Prepare payload
        payload = {
            "inputs": [test_case.model_dump() for test_case in inputs],
            "config": {
                eval_object.name: eval_object.config for eval_object in eval_templates
            },
        }

        # Make request
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=f"{self._base_url}/{Routes.evaluate.value}",
                json=payload,
                timeout=timeout or self._default_timeout,
            ),
            response_handler=EvalResponseHandler,
        )

        return response

    def _validate_inputs(
        self,
        inputs: List[TestCase],
        eval_objects: List[EvalTemplate],
    ):
        """
        Validate the inputs against the evaluation templates

        Args:
            inputs: List of test cases to validate
            eval_objects: List of evaluation templates to validate against

        Returns:
            bool: True if validation passes

        Raises:
            Exception: If validation fails or templates don't share common tags
        """

        # First validate that all eval objects share at least one common tag
        if len(eval_objects) > 1:
            # Get sets of tags for each eval object
            tag_sets = [set(obj.eval_tags) for obj in eval_objects]

            # Find intersection of all tag sets
            common_tags = set.intersection(*tag_sets)

            if not common_tags:
                template_names = [obj.name for obj in eval_objects]
                raise Exception(
                    f"Evaluation templates {template_names} must share at least one common tag. "
                    f"Current tags for each template: {[list(tags) for tags in tag_sets]}"
                )

        # Then validate each eval object's required inputs
        for eval_object in eval_objects:
            eval_object.validate_input(inputs)

        return True
