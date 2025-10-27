import os
import sys
import pytest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fi.evals.metrics import EmbeddingSimilarity
from fi.testcases import TestCase
from fi.evals.types import BatchRunResult


@pytest.fixture
def embedding_evaluator():
    """Create a default Embedding Similarity evaluator"""
    return EmbeddingSimilarity(config={
        "similarity_method": "cosine",
        "normalize": True,
        "model_name": "all-MiniLM-L6-v2"
    })


def test_embedding_similarity_with_identical_texts(embedding_evaluator):
    """Test embedding similarity calculation with identical texts"""
    test_case = TestCase(
        response="The quick brown fox jumps over the lazy dog",
        expected_text="The quick brown fox jumps over the lazy dog"
    )
    
    similarity = embedding_evaluator._calculate_embedding_similarity(test_case)
    assert similarity == 1.0, "Identical texts should have similarity score of 1.0"
    
    result = embedding_evaluator.evaluate([test_case])
    assert isinstance(result, BatchRunResult)
    assert len(result.eval_results) == 1
    assert result.eval_results[0].metrics[0].id == "embedding_similarity"
    assert result.eval_results[0].metrics[0].value == 1.0


def test_embedding_similarity_with_similar_texts(embedding_evaluator):
    """Test embedding similarity with semantically similar texts"""
    test_case = TestCase(
        response="A cat sat on the mat",
        expected_text="A cat was sitting on the rug"
    )
    
    similarity = embedding_evaluator._calculate_embedding_similarity(test_case)
    assert 0.7 < similarity < 1.0, "Similar texts should have high but not perfect similarity"


def test_embedding_similarity_with_different_texts(embedding_evaluator):
    """Test embedding similarity with semantically different texts"""
    test_case = TestCase(
        response="The weather is nice today",
        expected_text="Quantum physics explains the nature of the universe"
    )
    
    similarity = embedding_evaluator._calculate_embedding_similarity(test_case)
    assert similarity < 0.7, "Different texts should have lower similarity"


def test_embedding_similarity_with_different_methods():
    """Test embedding similarity with different similarity methods"""
    euclidean_eval = EmbeddingSimilarity(config={
        "similarity_method": "euclidean",
        "normalize": True
    })
    
    manhattan_eval = EmbeddingSimilarity(config={
        "similarity_method": "manhattan",
        "normalize": True
    })
    
    test_case = TestCase(
        response="A cat sat on the mat",
        expected_text="A cat was sitting on the rug"
    )
    
    euclidean_sim = euclidean_eval._calculate_embedding_similarity(test_case)
    manhattan_sim = manhattan_eval._calculate_embedding_similarity(test_case)
    
    assert 0 <= euclidean_sim <= 1, "Euclidean similarity should be between 0 and 1"
    assert 0 <= manhattan_sim <= 1, "Manhattan similarity should be between 0 and 1"


def test_batch_evaluation(embedding_evaluator):
    """Test batch evaluation of multiple test cases"""
    test_cases = [
        TestCase(
            response="The quick brown fox jumps over the lazy dog",
            expected_text="The quick brown fox jumps over the lazy dog"
        ),
        TestCase(
            response="A cat sat on the mat",
            expected_text="A cat was sitting on the rug" 
        ),
        TestCase(
            response="The weather is nice today",
            expected_text="Quantum physics explains the nature of the universe"
        )
    ]
    
    results = embedding_evaluator.evaluate(test_cases)
    assert isinstance(results, BatchRunResult)
    assert len(results.eval_results) == len(test_cases)
    
    assert results.eval_results[0].metrics[0].value == 1.0
    
    assert 0.7 < results.eval_results[1].metrics[0].value < 1.0
    
    assert results.eval_results[2].metrics[0].value < 0.7


def test_missing_required_fields():
    """Test that missing required fields raise an error"""
    embedding_eval = EmbeddingSimilarity()
    
    # Test case missing response
    with pytest.raises(ValueError, match=".*must have a 'response' field.*"):
        embedding_eval.validate_input([TestCase(expected_text="test")])
    
    # Test case missing expected_text
    with pytest.raises(ValueError, match=".*must have an 'expected_text' field.*"):
        embedding_eval.validate_input([TestCase(response="test")])


def test_empty_inputs(embedding_evaluator):
    """Test handling of empty inputs"""
    test_case = TestCase(
        response="",
        expected_text="reference"
    )
    
    similarity = embedding_evaluator._calculate_embedding_similarity(test_case)
    assert similarity == 0.0, "Empty response should have similarity of 0.0"
    
    test_case = TestCase(
        response="response",
        expected_text=""
    )
    
    similarity = embedding_evaluator._calculate_embedding_similarity(test_case)
    assert similarity == 0.0, "Empty reference should have similarity of 0.0"

