import os
from typing import List, Dict, Any

# ==============================================================================
# Setup: Add the project's Python path so we can import the necessary modules.
# ==============================================================================
import sys

# This assumes the script is run from the root of the `internal-futureagi-python` directory.
# Adjust the path if you place the script elsewhere.
project_root = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(project_root, "python")
if python_path not in sys.path:
    sys.path.insert(0, python_path)

# ==============================================================================
# Imports: Bring in the required classes from the `fi` library.
# ==============================================================================

from fi.evals.metrics import (
        Contains,
        LengthGreaterThan,
        Regex,
        ContainsAll,
        ContainsAny,
        ContainsNone,
        OneLine,
        ContainsEmail,
        IsEmail,
        ContainsLink,
        ContainsValidLink,
        Equals,
        StartsWith,
        EndsWith,
        LengthLessThan,
        LengthBetween,
        ContainsJson,
        IsJson,
        JsonSchema,
        BLEUScore,
        ROUGEScore,
        RecallScore,
        LevenshteinSimilarity,
        NumericSimilarity,
        EmbeddingSimilarity,
        SemanticListContains,
        AggregatedMetric,
    )
from fi.evals.metrics import CustomLLMJudge
from fi.evals.llm import LiteLLMProvider
from fi.evals.types import TextMetricInput, JsonMetricInput
from fi.evals.metrics.llm_as_judges import CustomInput



llm_provider = LiteLLMProvider()

# ==============================================================================
# Helper Function: A utility to print evaluation results in a readable format.
# ==============================================================================
def print_results(title: str, results: List[Dict[str, Any]]):
    """Prints the results of a metric evaluation in a formatted way."""
    print("-" * 80)
    print(f"Running: {title}")
    print("-" * 80)
    for i, result in enumerate(results):
        print(f"  Result {i + 1}:")
        # All results will have these keys from the BaseMetric `evaluate` method.
        print(f"    Name:   {result.name}")
        print(f"    Score:  {result.output}")
        print(f"    Reason: {result.reason}")
        print(f"    Runtime: {result.runtime} ms")
    print("\n")


# ==============================================================================
# Test Cases: Define the data and metrics for our tests.
# ==============================================================================

# --- 1. Heuristic Metric: Contains ---
# This metric checks if a given keyword is present in the response text.
def test_contains_metric():
    contains_metric = Contains(config={"keyword": "world", "case_sensitive": False})
    inputs = [
        TextMetricInput(response="Hello, world!"),  # Should pass (score 1.0)
        TextMetricInput(response="Hello, Universe!"),  # Should fail (score 0.0)
        TextMetricInput(response="HELLO, WORLD!"),  # Should pass (case-insensitive)
    ]
    results = contains_metric.evaluate(inputs)
    print_results("Heuristic Metric: Contains 'world'", results.eval_results)


# --- 2. Heuristic Metric: LengthGreaterThan ---
# This metric checks if the length of the response is greater than a specified minimum.
def test_length_greater_than_metric():
    length_metric = LengthGreaterThan(config={"min_length": 10})
    inputs = [
        TextMetricInput(response="This is a long sentence."),  # Should pass
        TextMetricInput(response="Short."),  # Should fail
        TextMetricInput(response="Exactly 11."),  # Should pass
    ]
    results = length_metric.evaluate(inputs)
    print_results("Heuristic Metric: LengthGreaterThan 10", results.eval_results)


# --- 3. Additional String Metrics ---
def test_all_string_metrics():
    # Regex
    regex_metric = Regex(config={"pattern": r"\d{3}-\d{2}-\d{4}"})
    inputs = [
        TextMetricInput(response="My SSN is 999-88-7777."),
        TextMetricInput(response="No SSN here."),
    ]
    print_results(
        "String Metric: Regex (SSN Pattern)", regex_metric.evaluate(inputs).eval_results
    )

    # ContainsAll
    contains_all_metric = ContainsAll(
        config={"keywords": ["hello", "world"], "case_sensitive": True}
    )
    inputs = [
        TextMetricInput(response="hello, world"),
        TextMetricInput(response="hello, universe"),
    ]
    print_results(
        "String Metric: ContainsAll", contains_all_metric.evaluate(inputs).eval_results
    )

    # ContainsAny
    contains_any_metric = ContainsAny(config={"keywords": ["apple", "banana"]})
    inputs = [
        TextMetricInput(response="I like apples."),
        TextMetricInput(response="I like oranges."),
    ]
    print_results(
        "String Metric: ContainsAny", contains_any_metric.evaluate(inputs).eval_results
    )

    # ContainsNone
    contains_none_metric = ContainsNone(config={"keywords": ["fail", "error"]})
    inputs = [
        TextMetricInput(response="Success!"),
        TextMetricInput(response="An error occurred."),
    ]
    print_results(
        "String Metric: ContainsNone",
        contains_none_metric.evaluate(inputs).eval_results,
    )

    # OneLine
    one_line_metric = OneLine()
    inputs = [
        TextMetricInput(response="This is one line."),
        TextMetricInput(response="This is\ntwo lines."),
    ]
    print_results("String Metric: OneLine", one_line_metric.evaluate(inputs).eval_results)

    # ContainsEmail
    contains_email_metric = ContainsEmail()
    inputs = [
        TextMetricInput(response="Contact me at test@example.com."),
        TextMetricInput(response="No email here."),
    ]
    print_results(
        "String Metric: ContainsEmail",
        contains_email_metric.evaluate(inputs).eval_results,
    )

    # IsEmail
    is_email_metric = IsEmail()
    inputs = [
        TextMetricInput(response="test@example.com"),
        TextMetricInput(response="not-an-email"),
    ]
    print_results("String Metric: IsEmail", is_email_metric.evaluate(inputs).eval_results)

    # ContainsLink
    contains_link_metric = ContainsLink()
    inputs = [
        TextMetricInput(response="Check out example.com for more info."),
        TextMetricInput(response="No links here."),
    ]
    print_results(
        "String Metric: ContainsLink",
        contains_link_metric.evaluate(inputs).eval_results,
    )

    # ContainsValidLink (Note: this makes a real network request)
    contains_valid_link_metric = ContainsValidLink()
    inputs = [
        TextMetricInput(response="Visit google.com."),  # Should be valid
        TextMetricInput(response="Go to a-domain-that-does-not-exist.com."),  # Invalid
    ]
    print_results(
        "String Metric: ContainsValidLink",
        contains_valid_link_metric.evaluate(inputs).eval_results,
    )

    # Equals
    equals_metric = Equals(config={"case_sensitive": False})
    inputs = [
        TextMetricInput(response="Hello", expected_response="hello"),
        TextMetricInput(response="Goodbye", expected_response="hello"),
    ]
    print_results("String Metric: Equals", equals_metric.evaluate(inputs).eval_results)

    # StartsWith
    starts_with_metric = StartsWith()
    inputs = [
        TextMetricInput(response="Hello, world", expected_response="Hello"),
        TextMetricInput(response="Hi there", expected_response="Hello"),
    ]
    print_results(
        "String Metric: StartsWith", starts_with_metric.evaluate(inputs).eval_results
    )

    # EndsWith
    ends_with_metric = EndsWith()
    inputs = [
        TextMetricInput(response="Hello, world", expected_response="world"),
        TextMetricInput(response="Hello, universe", expected_response="world"),
    ]
    print_results(
        "String Metric: EndsWith", ends_with_metric.evaluate(inputs).eval_results
    )

    # LengthLessThan
    length_less_than_metric = LengthLessThan(config={"max_length": 5})
    inputs = [TextMetricInput(response="Hi"), TextMetricInput(response="Hello")]
    print_results(
        "String Metric: LengthLessThan 5",
        length_less_than_metric.evaluate(inputs).eval_results,
    )

    # LengthBetween
    length_between_metric = LengthBetween(config={"min_length": 3, "max_length": 5})
    inputs = [
        TextMetricInput(response="Four"),
        TextMetricInput(response="Two"),
        TextMetricInput(response="Sixsix"),
    ]
    print_results(
        "String Metric: LengthBetween 3 and 5",
        length_between_metric.evaluate(inputs).eval_results,
    )


# --- 4. JSON Metrics ---
def test_all_json_metrics():
    # ContainsJson
    contains_json_metric = ContainsJson()
    inputs = [
        TextMetricInput(response='Some text {"key": "value"}'),
        TextMetricInput(response="No JSON here."),
    ]
    print_results(
        "JSON Metric: ContainsJson",
        contains_json_metric.evaluate(inputs).eval_results,
    )

    # IsJson
    is_json_metric = IsJson()
    inputs = [
        TextMetricInput(response='{"key": "value"}'),
        TextMetricInput(response='not json'),
    ]
    print_results("JSON Metric: IsJson", is_json_metric.evaluate(inputs).eval_results)

    # JsonSchema
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
        },
        "required": ["name", "age"],
    }
    json_schema_metric = JsonSchema()
    inputs = [
        JsonMetricInput(response='{"name": "John", "age": 30}', schema=schema),
        JsonMetricInput(response='{"name": "John"}', schema=schema),  # Missing 'age'
    ]
    print_results(
        "JSON Metric: JsonSchema", json_schema_metric.evaluate(inputs).eval_results
    )


# --- 5. Similarity Metrics ---
def test_all_similarity_metrics():
    # BLEUScore
    bleu_metric = BLEUScore()
    inputs = [
        TextMetricInput(
            response="the cat is on the mat",
            expected_response=["the cat is on the mat", "a cat is on the mat"],
        ),
        TextMetricInput(
            response="the dog is in the house",
            expected_response="the cat is on the mat",
        ),
    ]
    print_results("Similarity Metric: BLEUScore", bleu_metric.evaluate(inputs).eval_results)

    # ROUGEScore
    rouge_metric = ROUGEScore(config={"rouge_type": "rougeL"})
    inputs = [
        TextMetricInput(
            response="the cat is on the mat",
            expected_response="the cat sat on the mat",
        ),
    ]
    print_results("Similarity Metric: ROUGEScore", rouge_metric.evaluate(inputs).eval_results)

    # RecallScore
    recall_metric = RecallScore()
    inputs = [
        TextMetricInput(
            response='["apple", "banana"]',
            expected_response='["apple", "banana", "orange"]',
        ),
        TextMetricInput(
            response='["grape"]', expected_response='["apple", "banana"]'
        ),
    ]
    print_results(
        "Similarity Metric: RecallScore", recall_metric.evaluate(inputs).eval_results
    )

    # LevenshteinSimilarity
    levenshtein_metric = LevenshteinSimilarity()
    inputs = [
        TextMetricInput(response="kitten", expected_response="sitting"),
    ]
    print_results(
        "Similarity Metric: LevenshteinSimilarity",
        levenshtein_metric.evaluate(inputs).eval_results,
    )

    # NumericSimilarity
    numeric_metric = NumericSimilarity()
    inputs = [
        TextMetricInput(response="The price is 100.", expected_response="105"),
    ]
    print_results(
        "Similarity Metric: NumericSimilarity",
        numeric_metric.evaluate(inputs).eval_results,
    )

    # EmbeddingSimilarity
    # Note: This will download a sentence-transformer model on first run.
    try:
        embedding_metric = EmbeddingSimilarity()
        inputs = [
            TextMetricInput(
                response="The weather is nice.",
                expected_response="It is a sunny day.",
            ),
            TextMetricInput(
                response="I like to eat apples.",
                expected_response="The sky is blue.",
            ),
        ]
        print_results(
            "Similarity Metric: EmbeddingSimilarity",
            embedding_metric.evaluate(inputs).eval_results,
        )
    except ImportError as e:
        print(f"Skipping EmbeddingSimilarity test: {e}")

    # SemanticListContains
    try:
        semantic_list_metric = SemanticListContains(
            config={"similarity_threshold": 0.6}
        )
        inputs = [
            TextMetricInput(
                response="It's a beautiful, sunny day.",
                expected_response=["The weather is good.", "I am happy."],
            ),
        ]
        print_results(
            "Similarity Metric: SemanticListContains",
            semantic_list_metric.evaluate(inputs).eval_results,
        )
    except ImportError as e:
        print(f"Skipping SemanticListContains test: {e}")


# --- 6. Aggregated Metric ---
def test_aggregated_metric():
    # Define a few sub-metrics to aggregate
    contains_hello = Contains(config={"keyword": "hello"})
    is_one_line = OneLine()
    length_check = LengthGreaterThan(config={"min_length": 5})

    # Average Aggregation
    avg_metric = AggregatedMetric(
        config={
            "metrics": [contains_hello, is_one_line, length_check],
            "aggregator": "average",
        }
    )
    inputs = [
        TextMetricInput(response="hello world"),  # Pass: 1, 1, 1 -> Avg: 1.0
        TextMetricInput(response="hi\nthere"),  # Fail: 0, 0, 1 -> Avg: 0.33
        TextMetricInput(response="hi"),  # Fail: 0, 1, 0 -> Avg: 0.33
    ]
    print_results(
        "Aggregated Metric: Average", avg_metric.evaluate(inputs).eval_results
    )

    # Weighted Average Aggregation
    weighted_metric = AggregatedMetric(
        config={
            "metrics": [contains_hello, is_one_line, length_check],
            "aggregator": "weighted_average",
            "weights": [0.5, 0.2, 0.3],
        }
    )
    # Using the same inputs as above for comparison
    print_results(
        "Aggregated Metric: Weighted Average",
        weighted_metric.evaluate(inputs).eval_results,
    )


# --- 7. LLM-as-a-Judge Metric: CustomLLMJudge for Friendliness ---
# This metric uses an LLM to evaluate if a response is "friendly."
def test_llm_judge_friendliness():
    # The only required config is `grading_criteria`. The metric provides
    # sensible defaults for the prompt and output format.
    friendliness_judge = CustomLLMJudge(
        provider=llm_provider,
        config={
            "name": "friendliness_check",
            "model": "gpt-4o",  # Specify the model you want to use
            "grading_criteria": "Is the response friendly and welcoming? "
            "Score 1.0 for friendly, 0.0 for not friendly.",
        },
    )
    # Note: LLM-as-a-judge inputs are different. We use `CustomInput` here.
    inputs = [
        CustomInput(
            response="Hello there! It's a wonderful day, isn't it? How can I help you?"
        ),
        CustomInput(response="What do you want? State your request clearly."),
        CustomInput(
            response="Welcome to our service! We're so happy to have you here."
        ),
    ]

    try:
        results = friendliness_judge.evaluate(inputs)
        print_results("LLM-as-a-Judge: Friendliness Check", results.eval_results)
    except Exception as e:
        print("\n" + "-" * 80)
        print("An error occurred while running the LLM-as-a-Judge test.")
        print("This is often due to a missing or invalid API key.")
        print(f"Error details: {e}")
        print("-" * 80 + "\n")


# ==============================================================================
# Main Execution Block: Run all the defined test cases.
# ==============================================================================
if __name__ == "__main__":
    print("Starting metric evaluation tests...\n")

    # --- Basic Heuristics ---
    test_contains_metric()
    test_length_greater_than_metric()

    # --- Comprehensive String Metrics ---
    test_all_string_metrics()

    # --- JSON Validation Metrics ---
    test_all_json_metrics()

    # --- Similarity and Semantic Metrics ---
    test_all_similarity_metrics()

    # --- Aggregation of Multiple Metrics ---
    test_aggregated_metric()

    # --- LLM-as-a-Judge Evaluation ---
    # Note: This will make a real API call to an LLM provider.
    test_llm_judge_friendliness()

    print("\nAll tests completed.")