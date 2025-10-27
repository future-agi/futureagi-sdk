import os
import sys
import pytest
import json
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.testcases import TestCase
from fi.evals.metrics import SemanticListContains
from fi.evals.types import BatchRunResult

@pytest.fixture
def semantic_list_evaluator():
    """Create a SemanticListContains evaluator for testing"""
    return SemanticListContains(config={
        "case_insensitive": True,
        "remove_punctuation": True,
        "match_all": False,
        "similarity_threshold": 0.5
    })


def test_single_string_expected_text(semantic_list_evaluator):
    """Test using a single string for expected_text"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text="fox"
    )
    
    result, details = semantic_list_evaluator._check_semantic_containment(test_case)
    assert result is True, "Should match a single string reference"
    
    eval_result = semantic_list_evaluator.evaluate([test_case])
    assert isinstance(eval_result, BatchRunResult)
    assert len(eval_result.eval_results) == 1
    assert eval_result.eval_results[0].metrics[0].id == "semantic_list_contains"
    assert eval_result.eval_results[0].metrics[0].value == 1.0


def test_list_of_strings_expected_text(semantic_list_evaluator):
    """Test using a list of strings for expected_text (JSON-encoded)"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text=json.dumps(["brown fox", "lazy dog"])
    )
    
    result, details = semantic_list_evaluator._check_semantic_containment(test_case)
    assert result is True, "Should match phrases from a list"
    assert len(details["matches"]) == 2, "Should have results for both phrases"
    assert all(details["matches"]), "All phrases should match"
    
    eval_result = semantic_list_evaluator.evaluate([test_case])
    assert eval_result.eval_results[0].metrics[0].value == 1.0


def test_partial_matches(semantic_list_evaluator):
    """Test with a mix of matching and non-matching phrases"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text=json.dumps(["brown fox", "lazy dog", "flying elephant"])
    )
    
    # With match_all=False, should return True if any phrase matches
    result, details = semantic_list_evaluator._check_semantic_containment(test_case)
    assert result is True, "Should match with match_all=False if any phrase matches"
    assert not all(details["matches"]), "Not all phrases should match"
    
    strict_evaluator = SemanticListContains(config={
        "case_insensitive": True,
        "remove_punctuation": True,
        "match_all": True,
        "similarity_threshold": 0.5
    })
    
    result, details = strict_evaluator._check_semantic_containment(test_case)
    assert result is False, "Should not match with match_all=True if any phrase doesn't match"


def test_no_matches(semantic_list_evaluator):
    """Test with no matching phrases"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text=json.dumps(["flying elephant", "dancing giraffe"])
    )
    
    result, details = semantic_list_evaluator._check_semantic_containment(test_case)
    assert result is False, "Should not match when no phrases are similar"
    assert not any(details["matches"]), "No phrases should match"
    
    eval_result = semantic_list_evaluator.evaluate([test_case])
    assert eval_result.eval_results[0].metrics[0].value == 0.0


def test_batch_evaluation(semantic_list_evaluator):
    """Test batch evaluation of multiple test cases"""
    test_cases = [
        TestCase(
            response="The quick brown fox jumps over the lazy dog",
            expected_text="fox"
        ),
        TestCase(
            response="The quick brown fox jumps over the lazy dog",
            expected_text=json.dumps(["brown fox", "lazy dog"])
        ),
        TestCase(
            response="The quick brown fox jumps over the lazy dog",
            expected_text=json.dumps(["flying elephant", "dancing giraffe"])
        )
    ]
    
    results = semantic_list_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    # First test case should match
    assert results.eval_results[0].metrics[0].value == 1.0
    
    # Second test case should match
    assert results.eval_results[1].metrics[0].value == 1.0
    
    # Third test case should not match
    assert results.eval_results[2].metrics[0].value == 0.0


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    semantic_eval = SemanticListContains()
    
    # Test case missing response
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        semantic_eval.validate_input([TestCase(expected_text="test")])
    
    # Test case missing expected_text
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        semantic_eval.validate_input([TestCase(response="test")])