from typing import Any, Dict, List, Optional, Union

from requests_futures.sessions import FuturesSession

from fi.api.auth import APIKeyAuth
from fi.api.types import RequestType
from fi.bounded_executor import BoundedExecutor
from fi.evals.templates import EvalTemplate
from fi.evals.types import BatchRunResult, EvalResult, EvalResultMetric
from fi.testcases import ConversationalTestCase, LLMTestCase, MLLMTestCase, TestCase


class EvalClient(APIKeyAuth):
    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        url: Optional[str] = None,
        timeout: Optional[int] = 200,
        max_queue_bound: Optional[int] = 5000,
        max_workers: Optional[int] = 8,
    ) -> None:
        """
        Initialize the Eval Client

        Args:
            fi_api_key: API key
            fi_secret_key: Secret key
        """
        super().__init__(fi_api_key, fi_secret_key, url)

        self._timeout = timeout
        self._session = FuturesSession(
            executor=BoundedExecutor(max_queue_bound, max_workers)
        )

    @property
    def session(self):
        return self._session

    @property
    def url(self) -> str:
        return f"{self.BASE_URL}/sdk/api/v1/eval/"

    @property
    def headers(self) -> dict:
        return {
            "X-Api-Key": self._fi_api_key,
            "X-Secret-Key": self._fi_secret_key,
        }

    @property
    def payload(self) -> dict:
        if not hasattr(self, "_payload"):
            self._payload = {}
        return self._payload

    @property
    def params(self) -> dict:
        return {}

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
        timeout: Union[int, None] = None,
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
        """
        # Convert single items to lists for consistent handling
        if not isinstance(eval_templates, list):
            eval_templates = [eval_templates]
        if not isinstance(inputs, list):
            inputs = [inputs]

        # Validate inputs
        try:
            self._validate_inputs(inputs, eval_templates)
            self.payload.update(
                {
                    "inputs": [test_case.model_dump() for test_case in inputs],
                    "config": {},
                }
            )
            for eval_object in eval_templates:
                self.payload["config"][eval_object.name] = eval_object.config
        except Exception as e:
            raise e

        result = self.make_request(request_type=RequestType.POST.value)
        return self._validate_output(result)

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

    def _validate_output(self, result: Dict[str, Any]):
        if result.status_code == 200:
            return self.convert_to_batch_results(result.json())
        elif result.status_code == 400:
            raise Exception(result.json())
        else:
            raise Exception(result)

    def convert_to_batch_results(
        self, response: Dict[str, Any]
    ) -> List[BatchRunResult]:
        batch_results = []

        for result in response.get("result", []):
            for evaluation in result.get("evaluations", []):
                eval_result = EvalResult(
                    name=evaluation["name"],
                    display_name=evaluation["name"],
                    data=evaluation["data"],
                    failure=evaluation["failure"],
                    reason=evaluation["reason"],
                    runtime=evaluation["runtime"],
                    model=evaluation["model"],
                    metadata=evaluation["metadata"],
                    metrics=[
                        EvalResultMetric(id=metric["id"], value=metric["value"])
                        for metric in evaluation.get("metrics", [])
                    ],
                    datapoint_field_annotations=evaluation.get(
                        "datapointFieldAnnotations"
                    ),
                )
                batch_results.append(eval_result)

        batch_result = BatchRunResult(eval_results=batch_results)

        return batch_result
