import os
import sys
import pytest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import AggregatedMetric, BLEUScore, ROUGEScore
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def basic_metrics():
    """Create basic metrics for testing aggregation"""
    return [
        BLEUScore(config={"mode": "sentence"}),
        ROUGEScore(config={"rouge_type": "rouge1"})
    ]


def test_average_aggregation(basic_metrics):
    """Test aggregation with simple averaging"""
    aggregator = AggregatedMetric(config={
        "aggregator": "average",
        "metrics": basic_metrics
    })
    
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text="The brown fox jumped over the lazy dog"
    )
    
    result = aggregator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert result.eval_results[0].metrics[0].id == "aggregated_metric_score"
    
    score = result.eval_results[0].metrics[0].value
    assert 0 <= score <= 1, f"Score {score} should be between 0 and 1"
    
    metadata = result.eval_results[0].metadata
    assert "individual_scores" in metadata
    assert len(metadata["individual_scores"]) == len(basic_metrics)


def test_weighted_average_aggregation(basic_metrics):
    """Test aggregation with weighted averaging"""
    weights = [0.7, 0.3] 
    aggregator = AggregatedMetric(config={
        "aggregator": "weighted_average",
        "weights": weights,
        "metrics": basic_metrics
    })
    
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text="The brown fox jumped over the lazy dog"
    )
    
    result = aggregator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    
    score = result.eval_results[0].metrics[0].value
    assert 0 <= score <= 1, f"Score {score} should be between 0 and 1"
    
    metadata = result.eval_results[0].metadata
    assert metadata["weights"] == weights


def test_invalid_configuration():
    """Test with invalid configuration"""
    metrics = [BLEUScore()]
    
    with pytest.raises(AssertionError):
        AggregatedMetric(config={
            "aggregator": "weighted_average",
            "metrics": metrics
        })
    
    with pytest.raises(AssertionError):
        AggregatedMetric(config={
            "aggregator": "invalid_method",
            "metrics": metrics
        })
    
    with pytest.raises(ValueError):
        AggregatedMetric(config={
            "aggregator": "average",
            "metrics": []
        })


def test_batch_evaluation(basic_metrics):
    """Test batch evaluation with multiple test cases"""
    aggregator = AggregatedMetric(config={
        "aggregator": "average",
        "metrics": basic_metrics
    })
    
    test_cases = [
        TestCase(
            response="The quick brown fox jumps over the lazy dog",
            expected_text="The brown fox jumped over the lazy dog"
        ),
        TestCase(
            response="The weather today is sunny and warm",
            expected_text="Today's weather is sunny and warm"
        )
    ]
    
    results = aggregator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    for result in results.eval_results:
        score = result.metrics[0].value
        assert 0 <= score <= 1, f"Score {score} should be between 0 and 1"


def test_normalize_score():
    """Test score normalization"""
    aggregator = AggregatedMetric(config={
        "aggregator": "average",
        "metrics": [BLEUScore()]
    })
    
    assert aggregator._normalize_score(True) == 1.0
    assert aggregator._normalize_score(False) == 0.0
    assert aggregator._normalize_score(0.5) == 0.5
    assert aggregator._normalize_score(1.5) == 1.0 
    assert aggregator._normalize_score(-0.5) == 0.0 
    assert aggregator._normalize_score("not a number") == 0.0


def test_bleu_rouge_combination():
    """Test specific combination of BLEU and ROUGE metrics"""
    bleu = BLEUScore(config={"mode": "sentence", "max_n_gram": 2})
    rouge = ROUGEScore(config={"rouge_type": "rouge2"})
    
    aggregator = AggregatedMetric(config={
        "aggregator": "average",
        "metrics": [bleu, rouge]
    })
    
    test_case = TestCase(
        response="The cat sat on the mat",
        expected_text="A cat is sitting on the mat"
    )
    
    result = aggregator.evaluate([test_case])
    
    metadata = result.eval_results[0].metadata
    assert "BLEU Score" in metadata["individual_scores"]
    assert "ROUGE Score" in metadata["individual_scores"]
    
    bleu_score = metadata["individual_scores"]["BLEU Score"]
    rouge_score = metadata["individual_scores"]["ROUGE Score"]
    expected_avg = (bleu_score + rouge_score) / 2
    
    assert abs(result.eval_results[0].metrics[0].value - expected_avg) < 1e-10