import os
import sys
import pytest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import ROUGEScore
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def rouge_evaluator():
    """Create a default ROUGE evaluator"""
    return ROUGEScore(config={
        "rouge_type": "rouge1",
        "use_stemmer": True
    })


def test_rouge_score_with_string_reference(rouge_evaluator):
    """Test ROUGE score calculation with a single string reference"""
    test_case = TestCase(
        response="the cat is on the mat",
        expected_text="there is a cat on the mat"
    )
    
    scores = rouge_evaluator._calculate_rouge_score(test_case)
    
    assert "precision" in scores
    assert "recall" in scores
    assert "fmeasure" in scores
    
    for metric, value in scores.items():
        assert 0 <= value <= 1, f"ROUGE {metric} score should be between 0 and 1"
    
    result = rouge_evaluator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert len(result.eval_results[0].metrics) == 3  #precision, recall, fmeasure


def test_rouge_with_different_reference(rouge_evaluator):
    """Test ROUGE score calculation with different reference text"""
    test_case = TestCase(
        response="I am going to the store",
        expected_text="I will go to the market"
    )
    
    scores = rouge_evaluator._calculate_rouge_score(test_case)
    
    for metric, value in scores.items():
        assert 0 <= value <= 1, f"ROUGE {metric} score should be between 0 and 1"


def test_rouge_with_custom_config():
    """Test ROUGE with custom configuration"""
    custom_rouge = ROUGEScore(config={
        "rouge_type": "rouge2",
        "use_stemmer": False
    })
    
    test_case = TestCase(
        response="the cat is on the mat",
        expected_text="there is a cat on the mat"
    )
    
    scores = custom_rouge._calculate_rouge_score(test_case)
    
    assert "precision" in scores
    assert "recall" in scores
    assert "fmeasure" in scores


def test_batch_evaluation(rouge_evaluator):
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
    
    results = rouge_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    for result in results.eval_results:
        assert len(result.metrics) == 3
        for metric in result.metrics:
            assert 0 <= metric.value <= 1


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    rouge_eval = ROUGEScore()
    
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        rouge_eval.validate_input([TestCase(expected_text="test")])
    
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        rouge_eval.validate_input([TestCase(response="test")])


def test_empty_inputs():
    """Test handling of empty inputs"""
    rouge_eval = ROUGEScore()
    
    test_case = TestCase(
        response="",
        expected_text="reference text"
    )
    
    scores = rouge_eval._calculate_rouge_score(test_case)
    assert scores["precision"] == 0.0
    assert scores["recall"] == 0.0
    assert scores["fmeasure"] == 0.0
    
    test_case = TestCase(
        response="hypothesis text",
        expected_text=""
    )
    
    scores = rouge_eval._calculate_rouge_score(test_case)
    assert scores["precision"] == 0.0
    assert scores["recall"] == 0.0
    assert scores["fmeasure"] == 0.0


def test_identical_texts(rouge_evaluator):
    """Test ROUGE scores for identical texts (should be perfect)"""
    identical_text = "The quick brown fox jumps over the lazy dog"
    test_case = TestCase(
        response=identical_text,
        expected_text=identical_text
    )
    
    scores = rouge_evaluator._calculate_rouge_score(test_case)
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["fmeasure"] == 1.0
