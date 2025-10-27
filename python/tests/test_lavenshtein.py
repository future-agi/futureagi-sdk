import os
import sys
import pytest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import LevenshteinDistance
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def levenshtein_evaluator():
    """Create a default Levenshtein distance evaluator"""
    return LevenshteinDistance(config={
        "case_insensitive": False,
        "remove_punctuation": False
    })


def test_levenshtein_with_exact_match(levenshtein_evaluator):
    """Test Levenshtein distance calculation with exact match"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text="The quick brown fox jumps over the lazy dog"
    )
    
    distance = levenshtein_evaluator._calculate_levenshtein_distance(test_case)
    assert distance == 0.0, "Levenshtein distance should be 0.0 for identical strings"
    
    result = levenshtein_evaluator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert result.eval_results[0].metrics[0].id == "levenshtein_distance"
    assert result.eval_results[0].metrics[0].value == 0.0


def test_levenshtein_with_different_texts(levenshtein_evaluator):
    """Test Levenshtein distance calculation with different texts"""
    test_case = TestCase(
        response="kitten",
        expected_text="sitting"
    )
    
    distance = levenshtein_evaluator._calculate_levenshtein_distance(test_case)
    # Edit distance is 3, normalized by max length 7 ≈ 0.428
    assert 0.42 < distance < 0.43


def test_levenshtein_with_case_insensitive():
    """Test Levenshtein with case insensitive configuration"""
    case_insensitive_eval = LevenshteinDistance(config={
        "case_insensitive": True,
        "remove_punctuation": False
    })
    
    test_case = TestCase(
        response="The Quick Brown Fox",
        expected_text="the quick brown fox"
    )
    
    distance = case_insensitive_eval._calculate_levenshtein_distance(test_case)
    assert distance == 0.0, "Case-insensitive comparison should yield 0.0 distance"


def test_levenshtein_with_punctuation_removal():
    """Test Levenshtein with punctuation removal configuration"""
    no_punct_eval = LevenshteinDistance(config={
        "case_insensitive": False,
        "remove_punctuation": True
    })
    
    test_case = TestCase(
        response="Hello, world!",
        expected_text="Hello world"
    )
    
    distance = no_punct_eval._calculate_levenshtein_distance(test_case)
    assert distance == 0.0, "Punctuation removal should yield 0.0 distance"


def test_batch_evaluation(levenshtein_evaluator):
    """Test batch evaluation of multiple test cases"""
    test_cases = [
        TestCase(
            response="kitten",
            expected_text="sitting"
        ),
        TestCase(
            response="Hello world",
            expected_text="Hello, world!"
        ),
        TestCase(
            response="The quick brown fox",
            expected_text="The quick brown fox"
        )
    ]
    
    results = levenshtein_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    # First one should be around 0.428 (3/7)
    assert 0.42 < results.eval_results[0].metrics[0].value < 0.43
    
    # Second should have some distance due to punctuation
    assert results.eval_results[1].metrics[0].value > 0
    
    # Third should be exact match
    assert results.eval_results[2].metrics[0].value == 0.0


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    levenshtein_eval = LevenshteinDistance()
    
    # Test case missing response
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        levenshtein_eval.validate_input([TestCase(expected_text="test")])
    
    # Test case missing expected_text
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        levenshtein_eval.validate_input([TestCase(response="test")])


def test_empty_inputs(levenshtein_evaluator):
    """Test handling of empty inputs"""
    test_case = TestCase(
        response="",
        expected_text="reference"
    )
    
    distance = levenshtein_evaluator._calculate_levenshtein_distance(test_case)
    assert distance == 1.0, "Empty response should have normalized distance of 1.0"
    
    test_case = TestCase(
        response="response",
        expected_text=""
    )
    
    distance = levenshtein_evaluator._calculate_levenshtein_distance(test_case)
    assert distance == 1.0, "Empty reference should have normalized distance of 1.0"

