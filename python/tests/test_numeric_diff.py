import os
import sys
import pytest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import NumericDiff
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def numeric_diff_evaluator():
    """Create a default NumericDiff evaluator"""
    return NumericDiff(config={
        "extract_numeric": True,
        "normalized_result": True
    })


def test_numeric_diff_with_exact_numbers(numeric_diff_evaluator):
    """Test numeric difference calculation with exact numbers"""
    test_case = TestCase(
        response="42",
        expected_text="42"
    )
    
    diff = numeric_diff_evaluator._calculate_numeric_diff(test_case)
    assert diff == 0.0
    
    result = numeric_diff_evaluator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert result.eval_results[0].metrics[0].id == "numeric_diff"
    assert result.eval_results[0].metrics[0].value == 0.0


def test_numeric_diff_with_different_numbers(numeric_diff_evaluator):
    """Test numeric difference calculation with different numbers"""
    test_case = TestCase(
        response="50",
        expected_text="100"
    )
    
    diff = numeric_diff_evaluator._calculate_numeric_diff(test_case)
    assert diff == 0.5


def test_numeric_diff_with_text_extraction(numeric_diff_evaluator):
    """Test numeric extraction from text"""
    test_case = TestCase(
        response="The answer is 42 according to calculations",
        expected_text="The correct value should be 40"
    )
    
    diff = numeric_diff_evaluator._calculate_numeric_diff(test_case)
    assert diff == 0.05


def test_numeric_diff_with_custom_config():
    """Test NumericDiff with custom configuration"""
    custom_diff = NumericDiff(config={
        "extract_numeric": True,
        "normalized_result": False
    })
    
    test_case = TestCase(
        response="42",
        expected_text="30"
    )
    
    diff = custom_diff._calculate_numeric_diff(test_case)
    assert diff == 12.0


def test_batch_evaluation(numeric_diff_evaluator):
    """Test batch evaluation of multiple test cases"""
    test_cases = [
        TestCase(
            response="42",
            expected_text="42"
        ),
        TestCase(
            response="80",
            expected_text="100"
        ),
        TestCase(
            response="The answer is 75 percent",
            expected_text="Expected 70%"
        )
    ]
    
    results = numeric_diff_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    assert results.eval_results[0].metrics[0].value == 0.0
    assert results.eval_results[1].metrics[0].value == 0.2
    assert abs(results.eval_results[2].metrics[0].value - 0.071) < 0.01


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    numeric_diff_eval = NumericDiff()
    
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        numeric_diff_eval.validate_input([TestCase(expected_text="42")])
    
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        numeric_diff_eval.validate_input([TestCase(response="42")])


def test_no_numeric_values():
    """Test handling of inputs with no numeric values"""
    numeric_diff_eval = NumericDiff()
    
    test_case = TestCase(
        response="No numbers here",
        expected_text="Also no numbers"
    )
    
    results = numeric_diff_eval.evaluate([test_case])
    assert results.eval_results[0].failure is True
    assert "No numeric value found" in results.eval_results[0].reason
