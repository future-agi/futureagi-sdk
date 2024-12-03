from typing import Union

import pytest

from fi.evals import (
    AnswerSimilarity,
    DeterministicEvaluation,
    EvalClient,
    ImageInstruction,
    LengthBetween,
    ResponseFaithfulness,
)
from fi.evals.templates import RagasFaithfulness, RagasMaliciousness
from fi.evals.types import Comparator
from fi.testcases import LLMTestCase, MLLMImage, MLLMTestCase, TestCase


@pytest.fixture
def evaluator():
    return EvalClient()


def test_maliciousness(evaluator):
    test_case = LLMTestCase(
        query="Who is Prime Minister of India?", response="Narendra Modi"
    )
    template = RagasMaliciousness(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value is not None


def test_faithfulness(evaluator):
    test_case = LLMTestCase(
        query="Who is Prime Minister of India?",
        response="Narendra Modi",
        context="Narendra Modi is the Prime Minister of India",
    )
    template = RagasFaithfulness(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value is not None


def test_answer_similarity(evaluator):
    test_case = LLMTestCase(
        query="Who is Prime Minister of India?",
        response="Narendra Modi",
        context=["Narendra Modi is the Prime Minister of India"],
        expected_response="Narendra Modi",
    )
    template = AnswerSimilarity(
        config={"comparator": Comparator.COSINE.value, "failure_threshold": 0.8}
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value >= 0.8


def test_image_instruction(evaluator):
    test_case = MLLMTestCase(
        image_url="https://fastly.picsum.photos/id/199/200/300.jpg?hmac=GOJRy6ngeR2kvgwCS-aTH8bNUTZuddrykqXUW6AF2XQ",
        input=(
            "This is a serene beach landscape photo taken from a wooden boardwalk or "
            "stairs leading down to the sand. The composition shows the wooden railings in "
            "the foreground framing a view of a pristine sandy beach, turquoise-blue "
            "ocean waters, and a distant island or landmass on the horizon. The sky "
            "features soft, wispy clouds creating a peaceful atmosphere. The colors are "
            "somewhat muted and natural, giving the image a calm, tranquil feeling. The "
            "wooden structure appears to be weathered, suggesting it's a beach access "
            "point or viewing platform."
        ),
    )
    template = ImageInstruction(
        config={
            "criteria": (
                "The image should be a low angle close up shot of Aksel Adomas holding a "
                "box of cereal in a supermarket aisle with a confused expression."
            )
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value is not None


def test_response_faithfulness(evaluator):
    test_case = LLMTestCase(
        query="What is the image?",
        response="John Smith is holding a box of cereal in a supermarket aisle with a confused expression.",
        context="John Smith is holding a box of cereal in a supermarket aisle with a confused expression.",
    )
    template = ResponseFaithfulness(config={"model": "gpt-4o-mini"})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].metrics[0].value is not None


def test_length_between(evaluator):
    test_case = TestCase(
        text="This is a sample text that needs to be validated for length."
    )
    template = LengthBetween(config={"min_length": 10, "max_length": 100})
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert (
        response.eval_results[0].metrics[0].value == 1.0
    )  # Should pass as text length is within bounds


def test_deterministic_evaluation(evaluator):
    class DeterministicTestCase(TestCase):
        response: str
        expected_response: str

    test_case = DeterministicTestCase(
        response="Hello world", expected_response="Hello world"
    )
    template = DeterministicEvaluation(
        config={
            "multi_choice": False,
            "choices": ["Yes", "No"],
            "rule_prompt": "Evaluate if {{input_key1}} and {{input_key2}} are deterministic",
            "input": {"input_key1": "response", "input_key2": "expected_response"},
        }
    )
    response = evaluator.evaluate(eval_templates=[template], inputs=[test_case])

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].data[0] in ["Yes", "No"]


def test_deterministic_image_evaluation(evaluator):
    # Define test case class with image URLs
    class ImageDeterministicTestCase(MLLMTestCase):
        image_url: Union[str, MLLMImage]
        expected_label: str

    # Initialize the deterministic evaluator
    deterministic_eval = DeterministicEvaluation(
        config={
            "multi_choice": False,
            "choices": ["Yes", "No"],
            "rule_prompt": "Does the image at {{input_key1}} depict a stunning natural landscape featuring a narrow river winding through a deep canyon? Compare with expected answer {{input_key2}}",
            "input": {"input_key1": "image_url", "input_key2": "expected_label"},
        }
    )

    # Create a test case
    test_case = ImageDeterministicTestCase(
        image_url="https://fastly.picsum.photos/id/511/200/300.jpg?hmac=3pjxomHmNfWivxE47hYNY3VdnJTTJtcRJmQ3ihqJcBA",
        expected_label="Yes",
    )

    # Run the evaluation
    response = evaluator.evaluate(
        eval_templates=[deterministic_eval], inputs=[test_case]
    )

    assert response is not None
    assert len(response.eval_results) > 0
    assert response.eval_results[0].data[0] in ["Yes", "No"]
