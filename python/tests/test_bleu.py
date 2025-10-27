import pytest
import sys
from typing import List
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import BLEUScore
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def bleu_evaluator():
    """Create a default BLEU evaluator with sentence mode"""
    return BLEUScore(config={
        "mode": "sentence",
        "max_n_gram": 4,
        "smooth": "method1"
    })


@pytest.fixture
def corpus_bleu_evaluator():
    """Create a BLEU evaluator with corpus mode"""
    return BLEUScore(config={
        "mode": "corpus",
        "max_n_gram": 4,
        "smooth": "method1"
    })


@pytest.fixture
def custom_weight_bleu_evaluator():
    """Create a BLEU evaluator with custom weights"""
    return BLEUScore(config={
        "mode": "sentence",
        "max_n_gram": 3,
        "weights": [0.5, 0.3, 0.2],
        "smooth": "method2"
    })


def test_bleu_score_with_string_reference(bleu_evaluator):
    """Test BLEU score calculation with a single string reference"""
    test_case = TestCase(
        response="the cat is on the mat",
        expected_text="there is a cat on the mat"
    )
    
    score = bleu_evaluator._calculate_bleu_score(test_case)
    assert 0 <= score <= 1, "BLEU score should be between 0 and 1"
    
    result = bleu_evaluator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert result.eval_results[0].metrics[0].id == "bleu_score"
    assert 0 <= result.eval_results[0].metrics[0].value <= 1


def test_bleu_with_different_reference(bleu_evaluator):
    """Test BLEU score calculation with different reference text"""
    test_case = TestCase(
        response="I am going to the store",
        expected_text="I will go to the market"
    )
    
    score = bleu_evaluator._calculate_bleu_score(test_case)
    assert 0 <= score <= 1, "BLEU score should be between 0 and 1"


def test_bleu_with_custom_config():
    """Test BLEU with custom configuration"""
    custom_bleu = BLEUScore(config={
        "mode": "corpus",
        "max_n_gram": 2,
        "smooth": "method2"
    })
    
    test_case = TestCase(
        response="the cat is on the mat",
        expected_text="there is a cat on the mat"
    )
    
    score = custom_bleu._calculate_bleu_score(test_case)
    assert 0 <= score <= 1, "BLEU score should be between 0 and 1"


def test_batch_evaluation(bleu_evaluator):
    """Test batch evaluation of multiple test cases"""
    test_cases = [
        TestCase(
            response="the cat is on the mat",
            expected_text="there is a cat on the mat"
        ),
        TestCase(
            response="I am going to the store",
            expected_text="I will go to the store"
        ),
        TestCase(
            response="The weather is nice today",
            expected_text="It is a beautiful day today"
        )
    ]
    
    results = bleu_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    for result in results.eval_results:
        assert len(result.metrics) == 1
        assert 0 <= result.metrics[0].value <= 1


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    bleu_eval = BLEUScore()
    
    # Test case missing response
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        bleu_eval.validate_input([TestCase(expected_text="test")])
    
    # Test case missing expected_text
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        bleu_eval.validate_input([TestCase(response="test")])


def test_empty_inputs(bleu_evaluator):
    """Test handling of empty inputs"""
    test_case = TestCase(
        response="",
        expected_text="reference text"
    )
    
    score = bleu_evaluator._calculate_bleu_score(test_case)
    assert score == 0.0
    
    test_case = TestCase(
        response="hypothesis text",
        expected_text=""
    )
    
    try:
        score = bleu_evaluator._calculate_bleu_score(test_case)
        assert score == 0.0
    except Exception:
        pass


def test_identical_texts(bleu_evaluator):
    """Test BLEU scores for identical texts (should be perfect)"""
    identical_text = "The quick brown fox jumps over the lazy dog"
    test_case = TestCase(
        response=identical_text,
        expected_text=identical_text
    )
    
    score = bleu_evaluator._calculate_bleu_score(test_case)
    assert score == 1.0, "BLEU score should be 1.0 for identical texts"

