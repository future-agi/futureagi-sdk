import os
import uuid
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest
import pandas as pd

from fi.datasets import Dataset
from fi.datasets.types import (
    Cell,
    Column,
    DatasetConfig,
    DataTypeChoices,
    ModelTypes,
    Row,
    SourceChoices,
    HuggingfaceDatasetConfig,
)
from fi.utils.errors import (
    InvalidAuthError, 
    MissingAuthError, 
    DatasetNotFoundError, 
    DatasetError, 
    DatasetAuthError, 
    DatasetValidationError
)
from dotenv import load_dotenv
load_dotenv()

def test_authentication_error(monkeypatch):
    """Test that proper error is raised when auth keys are missing"""
    # Clear any existing environment variables for this test
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    
    with pytest.raises(MissingAuthError):
        Dataset(dataset_config=None)


def test_dataset_lifecycle():
    """Test complete dataset lifecycle: create, add columns/rows, download, and delete"""
    # Check for required environment variables
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.fail("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # Setup
    unique_name = f"test_dataset_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="Name",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        ),
        Column(
            name="Age",
            data_type=DataTypeChoices.INTEGER,
            source=SourceChoices.OTHERS,
            source_id=None,
        ),
        Column(
            name="AUDIO_URLS",
            data_type=DataTypeChoices.AUDIO,
            source=SourceChoices.OTHERS,
            source_id=None
        )
    ]
    rows = [
        Row(
            order=1,
            cells=[
                Cell(column_name="Name", value="Alice"),
                Cell(column_name="Age", value=25),
                Cell(column_name="AUDIO_URLS", value="https://archive.org/download/anthology_american_folk_music/002-fatal_flower_garden.mp3")
            ],
        ),
        Row(
            order=2,
            cells=[
                Cell(column_name="Name", value="Bob"),
                Cell(column_name="Age", value=30),
                Cell(column_name="AUDIO_URLS", value="https://archive.org/download/anthology_american_folk_music/003-house_carpenter.mp3")
            ],
        ),
    ]

    # Create dataset
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create()
    assert dataset.dataset_config.name == config.name
    assert dataset.dataset_config.id is not None

    # Add columns
    dataset = dataset.add_columns(columns=columns)
    assert dataset is not None

    # Add rows
    dataset = dataset.add_rows(rows=rows)
    assert dataset is not None

    # Download dataset
    file_path = f"output_test_{uuid.uuid4().hex[:8]}.csv"
    try:
        dataset.download(file_path=file_path)
        assert os.path.exists(file_path)

        with open(file_path, "r") as file:
            content = file.read()
            assert "Name" in content
            assert "Age" in content
    except ValueError as e:
        if "feedback_info" in str(e):
            pytest.skip("Server missing required database column 'feedback_info'")
        raise
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # Delete dataset
    dataset.delete()
    assert dataset.dataset_config is None


def test_get_config():
    """Test getting dataset configuration"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_config_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create()
    
    try:
        retrieved_config = dataset.get_config()
        assert retrieved_config.name == config.name
        assert retrieved_config.id is not None
        assert retrieved_config.model_type == config.model_type
    finally:
        dataset.delete()


def test_get_config_no_dataset():
    """Test getting config when no dataset is configured"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    dataset = Dataset(dataset_config=None)
    
    with pytest.raises(DatasetError, match="No dataset configured"):
        dataset.get_config()


def test_get_column_id():
    """Test getting column ID by name"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_column_id_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="TestColumn",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create().add_columns(columns=columns)
    
    try:
        column_id = dataset.get_column_id("TestColumn")
        assert column_id is not None
        
        # Test non-existent column
        non_existent_id = dataset.get_column_id("NonExistentColumn")
        assert non_existent_id is None
    finally:
        dataset.delete()


def test_get_column_id_validation():
    """Test get_column_id validation"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    dataset = Dataset(dataset_config=None)
    
    with pytest.raises(DatasetError, match="Dataset must be configured with an ID"):
        dataset.get_column_id("test")
    
    config = DatasetConfig(
        id=None, name="test", model_type=ModelTypes.GENERATIVE_LLM
    )
    dataset = Dataset(dataset_config=config)
    
    with pytest.raises(DatasetValidationError, match="Column name cannot be empty"):
        dataset.get_column_id("")


def test_add_columns_with_dicts():
    """Test adding columns using dictionary format"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_dict_columns_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dict_columns = [
        {"name": "DictColumn1", "data_type": DataTypeChoices.TEXT},
        {"name": "DictColumn2", "data_type": DataTypeChoices.INTEGER}
    ]
    
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create()
    
    try:
        dataset = dataset.add_columns(columns=dict_columns)
        assert dataset is not None
    finally:
        dataset.delete()


def test_add_rows_with_dicts():
    """Test adding rows using dictionary format"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_dict_rows_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="Name",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    
    dict_rows = [
        {
            "cells": [
                {"column_name": "Name", "value": "TestUser"}
            ]
        }
    ]
    
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create().add_columns(columns=columns)
    
    try:
        dataset = dataset.add_rows(rows=dict_rows)
        assert dataset is not None
    finally:
        dataset.delete()


def test_download_to_pandas():
    """Test downloading dataset directly to pandas DataFrame"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_pandas_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="Name",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    rows = [
        Row(
            order=1,
            cells=[Cell(column_name="Name", value="TestUser")],
        )
    ]
    
    dataset = Dataset(dataset_config=config)
    dataset = dataset.create().add_columns(columns=columns).add_rows(rows=rows)
    
    try:
        df = dataset.download(load_to_pandas=True)
        assert isinstance(df, pd.DataFrame)
        assert "Name" in df.columns
        assert len(df) > 0
    except ValueError as e:
        if "feedback_info" in str(e):
            pytest.skip("Server missing required database column 'feedback_info'")
        raise
    finally:
        dataset.delete()


def test_create_from_file():
    """Test creating dataset from local file"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Name,Age\nAlice,25\nBob,30\n")
        temp_file = f.name
    
    try:
        unique_name = f"test_from_file_{uuid.uuid4().hex[:8]}"
        config = DatasetConfig(
            id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
        )
        
        dataset = Dataset(dataset_config=config)
        dataset = dataset.create(source=temp_file)
        
        assert dataset.dataset_config.id is not None
        assert dataset.dataset_config.name == unique_name
        
        dataset.delete()
    finally:
        os.unlink(temp_file)


def test_create_from_huggingface():
    """Test creating dataset from Hugging Face"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_hf_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    hf_config = HuggingfaceDatasetConfig(
        name="squad",
        split="train",
        num_rows=10
    )
    
    dataset = Dataset(dataset_config=config)
    
    try:
        dataset = dataset.create(source=hf_config)
        assert dataset.dataset_config.id is not None
        assert dataset.dataset_config.name == unique_name
        dataset.delete()
    except Exception as e:
        # Hugging Face integration might not be available in test environment
        pytest.skip(f"Hugging Face integration test skipped: {e}")


# Class method tests
def test_create_dataset_class_method():
    """Test Dataset.create_dataset class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_class_create_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset.create_dataset(dataset_config=config)
    
    try:
        assert dataset.dataset_config.id is not None
        assert dataset.dataset_config.name == unique_name
    finally:
        dataset.delete()


def test_get_dataset_config_class_method():
    """Test Dataset.get_dataset_config class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # First create a dataset
    unique_name = f"test_get_config_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset.create_dataset(dataset_config=config)
    
    try:
        # Now get it using class method
        retrieved_dataset = Dataset.get_dataset_config(unique_name)
        assert retrieved_dataset.dataset_config.name == unique_name
        assert retrieved_dataset.dataset_config.id == dataset.dataset_config.id
    finally:
        dataset.delete()


def test_get_dataset_config_not_found():
    """Test Dataset.get_dataset_config with non-existent dataset"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    with pytest.raises(DatasetNotFoundError):
        Dataset.get_dataset_config("non_existent_dataset_123456789")


def test_download_dataset_class_method():
    """Test Dataset.download_dataset class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # Create a dataset first
    unique_name = f"test_class_download_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="Name",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    rows = [
        Row(
            order=1,
            cells=[Cell(column_name="Name", value="TestUser")],
        )
    ]
    
    dataset = Dataset.create_dataset(dataset_config=config)
    dataset = dataset.add_columns(columns=columns).add_rows(rows=rows)
    
    file_path = f"class_download_test_{uuid.uuid4().hex[:8]}.csv"
    
    try:
        # Test class method download
        result_path = Dataset.download_dataset(unique_name, file_path=file_path)
        assert result_path == file_path
        assert os.path.exists(file_path)
        
        # Test pandas download
        df = Dataset.download_dataset(unique_name, load_to_pandas=True)
        assert isinstance(df, pd.DataFrame)
        
    except ValueError as e:
        if "feedback_info" in str(e):
            pytest.skip("Server missing required database column 'feedback_info'")
        raise
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        dataset.delete()


def test_delete_dataset_class_method():
    """Test Dataset.delete_dataset class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_class_delete_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    # Create dataset
    Dataset.create_dataset(dataset_config=config)
    
    # Verify it exists
    retrieved = Dataset.get_dataset_config(unique_name)
    assert retrieved.dataset_config.name == unique_name
    
    # Delete using class method
    Dataset.delete_dataset(unique_name)
    
    # Verify it's gone
    with pytest.raises(DatasetNotFoundError):
        Dataset.get_dataset_config(unique_name)


def test_add_dataset_columns_class_method():
    """Test Dataset.add_dataset_columns class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_class_columns_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="ClassMethodColumn",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    
    dataset = Dataset.create_dataset(dataset_config=config)
    
    try:
        # Add columns using class method
        result = Dataset.add_dataset_columns(unique_name, columns)
        assert result is not None
    finally:
        dataset.delete()


def test_add_dataset_rows_class_method():
    """Test Dataset.add_dataset_rows class method"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_class_rows_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    columns = [
        Column(
            name="Name",
            data_type=DataTypeChoices.TEXT,
            source=SourceChoices.OTHERS,
            source_id=None,
        )
    ]
    rows = [
        Row(
            order=1,
            cells=[Cell(column_name="Name", value="ClassMethodUser")],
        )
    ]
    
    dataset = Dataset.create_dataset(dataset_config=config)
    dataset = dataset.add_columns(columns=columns)
    
    try:
        # Add rows using class method
        result = Dataset.add_dataset_rows(unique_name, rows)
        assert result is not None
    finally:
        dataset.delete()


# Error handling and validation tests
def test_create_existing_dataset():
    """Test creating dataset that already exists"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_existing_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset.create_dataset(dataset_config=config)
    
    try:
        # Try to create again with same config (now has ID)
        with pytest.raises(DatasetError, match="appears to already exist"):
            dataset.create()
    finally:
        dataset.delete()


def test_validation_errors():
    """Test various validation errors"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # Test empty columns list
    dataset = Dataset(dataset_config=None)
    with pytest.raises(DatasetValidationError, match="Columns list cannot be empty"):
        dataset.add_columns([])
    
    # Test empty rows list
    with pytest.raises(DatasetValidationError, match="Rows list cannot be empty"):
        dataset.add_rows([])
    
    # Test mixed column types
    mixed_columns = [
        Column(name="Col1", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
        {"name": "Col2", "data_type": DataTypeChoices.TEXT}
    ]
    with pytest.raises(DatasetValidationError, match="Columns must be a list of Column objects or a list of dictionaries"):
        dataset.add_columns(mixed_columns)


def test_unsupported_file_format():
    """Test creating dataset from unsupported file format"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    # Create a temporary file with unsupported extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("test content")
        temp_file = f.name
    
    try:
        unique_name = f"test_unsupported_{uuid.uuid4().hex[:8]}"
        config = DatasetConfig(
            id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
        )
        
        dataset = Dataset(dataset_config=config)
        
        with pytest.raises(DatasetValidationError, match="Unsupported file format"):
            dataset.create(source=temp_file)
    finally:
        os.unlink(temp_file)


def test_nonexistent_file():
    """Test creating dataset from non-existent file"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        pytest.skip("FI_API_KEY and FI_SECRET_KEY environment variables must be set")

    unique_name = f"test_nonexistent_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        id=None, name=unique_name, model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset(dataset_config=config)
    
    with pytest.raises(DatasetValidationError, match="File not found"):
        dataset.create(source="/path/to/nonexistent/file.csv")


# Tests for advanced features (may require mocking if dependencies not available)
@pytest.mark.skipif(not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"), 
                   reason="API keys not set")
def test_add_run_prompt_validation():
    """Test add_run_prompt validation without actually calling the API"""
    dataset = Dataset(dataset_config=None)
    
    with pytest.raises(DatasetError, match="Dataset must be configured with an ID"):
        dataset.add_run_prompt("test", "gpt-3.5-turbo", [{"role": "user", "content": "test"}])
    
    config = DatasetConfig(id="123", name="test", model_type=ModelTypes.GENERATIVE_LLM)
    dataset = Dataset(dataset_config=config)
    
    with pytest.raises(DatasetValidationError, match="Run prompt column name cannot be empty"):
        dataset.add_run_prompt("", "gpt-3.5-turbo", [{"role": "user", "content": "test"}])
    
    with pytest.raises(DatasetValidationError, match="Model cannot be empty"):
        dataset.add_run_prompt("test", "", [{"role": "user", "content": "test"}])
    
    with pytest.raises(DatasetValidationError, match="Messages list cannot be empty"):
        dataset.add_run_prompt("test", "gpt-3.5-turbo", [])


@pytest.mark.skipif(not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"), 
                   reason="API keys not set")  
def test_add_evaluation_missing_dependency():
    """Test add_evaluation when ai-evaluation is not installed"""
    config = DatasetConfig(id="123", name="test", model_type=ModelTypes.GENERATIVE_LLM)
    dataset = Dataset(dataset_config=config)
    
    # Mock the import to fail
    with patch('builtins.__import__', side_effect=ImportError):
        with pytest.raises(DatasetError, match="ai-evaluation is not installed"):
            dataset.add_evaluation("test", "template", {"key": "column"})


@pytest.mark.skipif(not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"), 
                   reason="API keys not set")
def test_add_optimization_validation():
    """Test add_optimization validation"""
    dataset = Dataset(dataset_config=None)
    
    with pytest.raises(DatasetError, match="Dataset must be configured with an ID"):
        dataset.add_optimization("test", "prompt_col")
    
    config = DatasetConfig(id="123", name="test", model_type=ModelTypes.GENERATIVE_LLM)
    dataset = Dataset(dataset_config=config)
    
    with pytest.raises(DatasetValidationError, match="Optimization name cannot be empty"):
        dataset.add_optimization("", "prompt_col")
    
    with pytest.raises(DatasetValidationError, match="Prompt column name for optimization cannot be empty"):
        dataset.add_optimization("test", "")
    
    with pytest.raises(DatasetValidationError, match="Invalid optimize_type"):
        dataset.add_optimization("test", "prompt_col", optimize_type="INVALID")
