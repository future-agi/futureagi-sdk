"""
Comprehensive Dataset Usage Examples

This file demonstrates various ways to use the Dataset class from the FutureAGI SDK.
It covers dataset creation, manipulation, evaluation, and optimization workflows.

Prerequisites:
- Set FI_API_KEY and FI_SECRET_KEY environment variables
- Install the FutureAGI SDK: pip install futureagi

Examples included:
1. Basic dataset operations (create, add data, download, delete)
2. Creating datasets from different sources (empty, file, Hugging Face)
3. Adding and running prompt columns
4. Adding evaluations and getting statistics
5. Setting up optimizations
6. Error handling and best practices
"""

import os
import uuid
import pandas as pd
from typing import Dict, List, Any

from fi.datasets import Dataset
from fi.datasets.types import (
    Cell,
    Column,
    DatasetConfig,
    DataTypeChoices,
    HuggingfaceDatasetConfig,
    ModelTypes,
    Row,
    SourceChoices,
)
from fi.utils.errors import (
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
    MissingAuthError,
)


def check_environment():
    """Check if required environment variables are set"""
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        raise MissingAuthError(
            "FI_API_KEY and FI_SECRET_KEY environment variables must be set",
            fi_secret_key=""
        )
    print("✓ Environment variables are set")


def example_1_basic_dataset_lifecycle():
    """
    Example 1: Basic Dataset Lifecycle
    
    Demonstrates:
    - Creating an empty dataset
    - Adding columns with different data types
    - Adding rows with data
    - Downloading the dataset
    - Deleting the dataset
    """
    print("\n=== Example 1: Basic Dataset Lifecycle ===")
    
    # Create a unique dataset name
    unique_name = f"basic_example_{uuid.uuid4().hex[:8]}"
    
    # Step 1: Create dataset configuration
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    # Step 2: Initialize dataset instance
    dataset = Dataset(dataset_config=config)
    
    try:
        # Step 3: Create empty dataset
        print(f"Creating dataset: {unique_name}")
        dataset = dataset.create()
        print(f"✓ Dataset created with ID: {dataset.dataset_config.id if dataset.dataset_config else 'Unknown'}")
        
        # Step 4: Define columns with various data types
        columns: List[Column] = [
            Column(
                name="user_query",
                data_type=DataTypeChoices.TEXT,
                source=SourceChoices.OTHERS
            ),
            Column(
                name="response_quality",
                data_type=DataTypeChoices.INTEGER,
                source=SourceChoices.OTHERS
            ),
            Column(
                name="is_helpful",
                data_type=DataTypeChoices.BOOLEAN,
                source=SourceChoices.OTHERS
            ),
            Column(
                name="response_time",
                data_type=DataTypeChoices.FLOAT,
                source=SourceChoices.OTHERS
            ),
            Column(
                name="metadata",
                data_type=DataTypeChoices.JSON,
                source=SourceChoices.OTHERS
            )
        ]
        
        # Step 5: Add columns to dataset
        print("Adding columns...")
        dataset = dataset.add_columns(columns=columns)  # type: ignore
        print("✓ Columns added successfully")
        
        # Step 6: Define sample data rows
        rows: List[Row] = [
            Row(
                order=1,
                cells=[
                    Cell(column_name="user_query", value="What is machine learning?"),
                    Cell(column_name="response_quality", value=8),
                    Cell(column_name="is_helpful", value=True),
                    Cell(column_name="response_time", value=1.2),
                    Cell(column_name="metadata", value='{"model": "gpt-4", "tokens": 150}')
                ]
            ),
            Row(
                order=2,
                cells=[
                    Cell(column_name="user_query", value="Explain quantum computing"),
                    Cell(column_name="response_quality", value=9),
                    Cell(column_name="is_helpful", value=True),
                    Cell(column_name="response_time", value=2.1),
                    Cell(column_name="metadata", value='{"model": "gpt-4", "tokens": 200}')
                ]
            ),
            Row(
                order=3,
                cells=[
                    Cell(column_name="user_query", value="What's the weather?"),
                    Cell(column_name="response_quality", value=5),
                    Cell(column_name="is_helpful", value=False),
                    Cell(column_name="response_time", value=0.8),
                    Cell(column_name="metadata", value='{"model": "gpt-3.5", "tokens": 50}')
                ]
            )
        ]
        
        # Step 7: Add rows to dataset
        print("Adding rows...")
        dataset = dataset.add_rows(rows=rows)  # type: ignore
        print("✓ Rows added successfully")
        
        # Step 8: Download dataset as CSV
        output_file = f"basic_example_{uuid.uuid4().hex[:8]}.csv"
        print(f"Downloading dataset to {output_file}...")
        dataset.download(file_path=output_file)
        print(f"✓ Dataset downloaded to {output_file}")
        
        # Step 9: Load as pandas DataFrame
        print("Loading dataset as pandas DataFrame...")
        df = dataset.download(load_to_pandas=True)
        if isinstance(df, pd.DataFrame):
            print(f"✓ Dataset loaded as DataFrame with shape: {df.shape}")
            print("First few rows:")
            print(df.head())
        else:
            print("✓ Dataset downloaded but not as DataFrame")
        
        # Cleanup downloaded file
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"✓ Cleaned up {output_file}")
            
    except Exception as e:
        print(f"✗ Error in basic lifecycle: {e}")
    finally:
        # Step 10: Delete dataset
        try:
            dataset.delete()
            print("✓ Dataset deleted successfully")
        except Exception as e:
            print(f"✗ Error deleting dataset: {e}")


def example_2_create_from_file():
    """
    Example 2: Creating Dataset from Local File
    
    Demonstrates:
    - Creating a sample CSV file
    - Creating dataset from local file
    - Working with file-based datasets
    """
    print("\n=== Example 2: Creating Dataset from File ===")
    
    # Step 1: Create sample CSV file
    sample_data = {
        "question": [
            "What is AI?",
            "How does machine learning work?",
            "What are neural networks?"
        ],
        "answer": [
            "AI is artificial intelligence...",
            "Machine learning uses algorithms...",
            "Neural networks are computing systems..."
        ],
        "category": ["general", "technical", "technical"],
        "difficulty": [1, 3, 4]
    }
    
    sample_file = f"sample_data_{uuid.uuid4().hex[:8]}.csv"
    df = pd.DataFrame(sample_data)
    df.to_csv(sample_file, index=False)
    print(f"✓ Created sample file: {sample_file}")
    
    # Step 2: Create dataset from file
    unique_name = f"file_example_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    try:
        dataset = Dataset.create_dataset(
            dataset_config=config,
            source=sample_file
        )
        print(f"✓ Dataset created from file with ID: {dataset.dataset_config.id}")
        
        # Download and verify
        output_file = f"file_output_{uuid.uuid4().hex[:8]}.csv"
        dataset.download(file_path=output_file)
        
        # Compare original and downloaded
        original_df = pd.read_csv(sample_file)
        downloaded_df = pd.read_csv(output_file)
        print(f"✓ Original shape: {original_df.shape}, Downloaded shape: {downloaded_df.shape}")
        
        # Cleanup
        os.remove(sample_file)
        os.remove(output_file)
        dataset.delete()
        print("✓ Cleanup completed")
        
    except Exception as e:
        print(f"✗ Error creating from file: {e}")
        # Cleanup on error
        if os.path.exists(sample_file):
            os.remove(sample_file)


def example_3_create_from_huggingface():
    """
    Example 3: Creating Dataset from Hugging Face
    
    Demonstrates:
    - Creating dataset from Hugging Face dataset
    - Working with different splits, subsets, and row limits
    """
    print("\n=== Example 3: Creating Dataset from Hugging Face ===")
    
    unique_name = f"hf_example_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    # Configure Hugging Face dataset with subset parameter
    hf_config = HuggingfaceDatasetConfig(
        name="squad",  # Stanford Question Answering Dataset
        subset="v2.0",  # Specify subset (e.g., v1.1, v2.0 for SQuAD)
        split="train",
        num_rows=10  # Limit to 10 rows for demo
    )
    
    try:
        print("Creating dataset from Hugging Face...")
        dataset = Dataset.create_dataset(
            dataset_config=config,
            source=hf_config
        )
        print(f"✓ Dataset created from Hugging Face with ID: {dataset.dataset_config.id}")
        
        # Download as DataFrame to inspect
        df = dataset.download(load_to_pandas=True)
        print(f"✓ Dataset shape: {df.shape}")
        print("Columns:", list(df.columns))
        print("Sample data:")
        print(df.head(2))
        
        dataset.delete()
        print("✓ Dataset deleted")
        
    except Exception as e:
        print(f"✗ Error creating from Hugging Face: {e}")


def example_4_prompt_columns_and_evaluation():
    """
    Example 4: Adding Prompt Columns and Evaluations
    
    Demonstrates:
    - Adding run prompt columns
    - Adding evaluations
    - Getting evaluation statistics
    """
    print("\n=== Example 4: Prompt Columns and Evaluation ===")
    
    unique_name = f"eval_example_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset(dataset_config=config)
    
    try:
        # Create dataset and add initial data
        dataset = dataset.create()
        print(f"✓ Dataset created: {dataset.dataset_config.name}")
        
        # Add input columns
        columns = [
            Column(
                name="user_question",
                data_type=DataTypeChoices.TEXT,
                source=SourceChoices.OTHERS
            ),
            Column(
                name="context",
                data_type=DataTypeChoices.TEXT,
                source=SourceChoices.OTHERS
            )
        ]
        dataset = dataset.add_columns(columns=columns)
        
        # Add sample data
        rows = [
            Row(
                order=1,
                cells=[
                    Cell(column_name="user_question", value="What is the capital of France?"),
                    Cell(column_name="context", value="France is a country in Europe with Paris as its capital.")
                ]
            ),
            Row(
                order=2,
                cells=[
                    Cell(column_name="user_question", value="How do you make coffee?"),
                    Cell(column_name="context", value="Coffee is made by brewing ground coffee beans with hot water.")
                ]
            )
        ]
        dataset = dataset.add_rows(rows=rows)
        print("✓ Initial data added")
        
        # Add a run prompt column
        print("Adding run prompt column...")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer questions based on the provided context."
            },
            {
                "role": "user",
                "content": "Context: {{context}}\n\nQuestion: {{user_question}}\n\nAnswer:"
            }
        ]
        
        dataset = dataset.add_run_prompt(
            name="ai_response",
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        print("✓ Run prompt column added")
        
        # Add evaluation
        print("Adding evaluation...")
        dataset = dataset.add_evaluation(
            name="response_length_check",
            eval_template="LengthGreaterThan",
            required_keys_to_column_names={
                "text": "ai_response"
            },
            config={"min_length": 10},
            run=True
        )
        print("✓ Evaluation added")
        
        # Get evaluation statistics
        print("Getting evaluation statistics...")
        eval_stats = dataset.get_eval_stats()
        print(f"✓ Evaluation stats retrieved: {len(eval_stats)} metrics")
        
    except Exception as e:
        print(f"✗ Error in prompt/evaluation example: {e}")
    finally:
        try:
            dataset.delete()
            print("✓ Dataset deleted")
        except:
            pass


def example_5_optimization():
    """
    Example 5: Dataset Optimization
    
    Demonstrates:
    - Setting up optimization for prompt templates
    - Working with evaluation metrics for optimization
    - Proper error handling and dataset cleanup
    """
    print("\n=== Example 5: Dataset Optimization ===")
    
    unique_name = f"opt_example_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    dataset = Dataset(dataset_config=config)
    
    try:
        # Create and setup dataset
        dataset = dataset.create()
        if dataset.dataset_config:
            print(f"✓ Dataset created: {dataset.dataset_config.name}")
        else:
            print("✗ Failed to create dataset - no configuration returned")
            return
        
        # Add columns using proper type casting
        columns: List[Column] = [
            Column(name="input_text", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
            Column(name="expected_output", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS)
        ]
        dataset = dataset.add_columns(columns=columns)
        print("✓ Columns added successfully")
        
        # Add data using proper type casting
        rows: List[Row] = [
            Row(
                order=1,
                cells=[
                    Cell(column_name="input_text", value="Summarize this article about climate change"),
                    Cell(column_name="expected_output", value="A concise summary focusing on key climate impacts")
                ]
            ),
            Row(
                order=2,
                cells=[
                    Cell(column_name="input_text", value="Explain quantum computing"),
                    Cell(column_name="expected_output", value="A clear explanation suitable for beginners")
                ]
            ),
            Row(
                order=3,
                cells=[
                    Cell(column_name="input_text", value="Write a brief introduction to machine learning"),
                    Cell(column_name="expected_output", value="An accessible introduction covering basic concepts")
                ]
            )
        ]
        dataset = dataset.add_rows(rows=rows)
        print("✓ Sample data added successfully")
        
        # Add prompt column with proper message structure
        messages = [
            {
                "role": "system",
                "content": "You are an expert assistant. Provide clear and helpful responses."
            },
            {
                "role": "user",
                "content": "{{input_text}}"
            }
        ]
        
        print("Adding run prompt column...")
        dataset = dataset.add_run_prompt(
            name="optimized_response",
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=200
        )
        print("✓ Run prompt column added successfully")
        
        # Add evaluation for optimization - using a more reliable evaluation template
        print("Adding evaluation for optimization...")
        dataset = dataset.add_evaluation(
            name="response_quality_check",
            eval_template="LengthGreaterThan",
            required_keys_to_column_names={
                "text": "optimized_response"
            },
            config={"min_length": 20},  # Ensure responses are at least 20 characters
            run=True
        )
        print("✓ Evaluation added successfully")
        
        # Wait a moment for evaluation to process
        import time
        print("Waiting for evaluation to process...")
        time.sleep(5)  # Increased wait time
        
        # Check if evaluations are available before optimization
        print("Checking available evaluations...")
        try:
            eval_stats = dataset.get_eval_stats()
            print(f"Available evaluations: {len(eval_stats) if isinstance(eval_stats, list) else 'Unknown'}")
        except Exception as e:
            print(f"Could not get evaluation stats: {e}")
        
        # Setup optimization with corrected payload format
        print("Setting up optimization...")
        try:
            dataset = dataset.add_optimization(
                optimization_name="prompt_optimization_example",
                prompt_column_name="optimized_response",
                optimize_type="PROMPT_TEMPLATE",
                model_config={
                    "model_name": "gpt-4o-mini",  # Include model_name as required
                    "temperature": 0.3,
                    "max_tokens": 300,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "top_p": 1.0
                }
            )
        except DatasetError as opt_error:
            print(f"Optimization setup failed: {opt_error}")
            print("This might be due to:")
            print("1. Evaluations not fully processed yet")
            print("2. Column not properly linked to evaluations")
            print("3. Backend timing issues")
            print("Trying alternative approach...")
            
            # Alternative: Try with a longer wait and retry
            print("Waiting longer for backend processing...")
            time.sleep(10)
            
            dataset = dataset.add_optimization(
                optimization_name="prompt_optimization_example",
                prompt_column_name="optimized_response",
                optimize_type="PROMPT_TEMPLATE",
                model_config={
                    "model_name": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 300,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "top_p": 1.0
                }
            )
        print("✓ Optimization setup completed successfully!")
        print("  - Optimization Name: prompt_optimization_example")
        print("  - Target Column: optimized_response")
        print("  - Optimization Type: PROMPT_TEMPLATE")
        print("  - Model Configuration: Updated with enhanced parameters")
        
    except DatasetError as e:
        print(f"✗ Dataset Error in optimization example: {e}")
        print("  This might be due to missing evaluations or incorrect column references")
    except DatasetValidationError as e:
        print(f"✗ Validation Error in optimization example: {e}")
        print("  Check that all required fields are properly formatted")
    except Exception as e:
        print(f"✗ Unexpected error in optimization example: {e}")
        print(f"  Error type: {type(e).__name__}")
    finally:
        try:
            if dataset and dataset.dataset_config:
                dataset.delete()
                print("✓ Dataset deleted successfully")
        except Exception as cleanup_error:
            print(f"✗ Error during cleanup: {cleanup_error}")


def example_6_class_methods():
    """
    Example 6: Using Class Methods for Simple Operations
    
    Demonstrates:
    - Using class methods for one-off operations
    - Getting dataset configurations
    - Simple download and delete operations
    """
    print("\n=== Example 6: Class Methods for Simple Operations ===")
    
    # First create a dataset to work with
    unique_name = f"class_methods_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    try:
        # Create using class method
        dataset = Dataset.create_dataset(dataset_config=config)
        print(f"✓ Dataset created using class method: {dataset.dataset_config.name}")
        
        # Add some data using class methods
        columns = [
            {"name": "text", "data_type": DataTypeChoices.TEXT},
            {"name": "score", "data_type": DataTypeChoices.INTEGER}
        ]
        
        Dataset.add_dataset_columns(
            dataset_name=unique_name,
            columns=columns
        )
        print("✓ Columns added using class method")
        
        rows = [
            {
                "cells": [
                    {"column_name": "text", "value": "Sample text 1"},
                    {"column_name": "score", "value": 85}
                ]
            },
            {
                "cells": [
                    {"column_name": "text", "value": "Sample text 2"},
                    {"column_name": "score", "value": 92}
                ]
            }
        ]
        
        Dataset.add_dataset_rows(
            dataset_name=unique_name,
            rows=rows
        )
        print("✓ Rows added using class method")
        
        # Get dataset configuration
        dataset_instance = Dataset.get_dataset_config(unique_name)
        print(f"✓ Retrieved dataset config: {dataset_instance.dataset_config.name}")
        
        # Download using class method
        output_file = f"class_method_output_{uuid.uuid4().hex[:8]}.csv"
        Dataset.download_dataset(
            dataset_name=unique_name,
            file_path=output_file
        )
        print(f"✓ Dataset downloaded using class method to {output_file}")
        
        # Cleanup file
        if os.path.exists(output_file):
            os.remove(output_file)
        
        # Delete using class method
        Dataset.delete_dataset(unique_name)
        print("✓ Dataset deleted using class method")
        
    except Exception as e:
        print(f"✗ Error in class methods example: {e}")


def example_7_error_handling():
    """
    Example 7: Error Handling and Best Practices
    
    Demonstrates:
    - Common error scenarios
    - Proper error handling
    - Best practices for dataset operations
    """
    print("\n=== Example 7: Error Handling and Best Practices ===")
    
    # Test 1: Dataset not found
    try:
        Dataset.get_dataset_config("nonexistent_dataset_12345")
    except DatasetNotFoundError as e:
        print(f"✓ Correctly caught DatasetNotFoundError: {e}")
    
    # Test 2: Invalid dataset configuration
    try:
        invalid_config = DatasetConfig(
            name="",  # Empty name should fail validation
            model_type=ModelTypes.GENERATIVE_LLM
        )
    except ValueError as e:
        print(f"✓ Correctly caught validation error: {e}")
    
    # Test 3: Adding columns to non-existent dataset
    try:
        dataset = Dataset()  # No config
        dataset.add_columns([
            Column(name="test", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS)
        ])
    except DatasetError as e:
        print(f"✓ Correctly caught DatasetError: {e}")
    
    # Test 4: Best practice - using context managers for cleanup
    unique_name = f"error_handling_{uuid.uuid4().hex[:8]}"
    config = DatasetConfig(
        name=unique_name,
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    class DatasetContext:
        def __init__(self, config):
            self.config = config
            self.dataset = None
            
        def __enter__(self):
            self.dataset = Dataset(dataset_config=self.config)
            self.dataset = self.dataset.create()
            return self.dataset
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.dataset and self.dataset.dataset_config:
                try:
                    self.dataset.delete()
                    print("✓ Dataset cleaned up automatically")
                except:
                    pass
    
    # Use context manager for automatic cleanup
    try:
        with DatasetContext(config) as dataset:
            print(f"✓ Dataset created with automatic cleanup: {dataset.dataset_config.name}")
            # Do work with dataset
            columns = [Column(name="test_col", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS)]
            dataset.add_columns(columns=columns)
            print("✓ Operations completed successfully")
            # Dataset will be automatically deleted when exiting context
    except Exception as e:
        print(f"✗ Error in context manager example: {e}")


def main():
    """Run all examples"""
    print("FutureAGI Dataset SDK - Comprehensive Usage Examples")
    print("=" * 60)
    
    try:
        # Check environment setup
        check_environment()
        
        # Run all examples
        example_1_basic_dataset_lifecycle()
        example_2_create_from_file()
        example_3_create_from_huggingface()
        example_4_prompt_columns_and_evaluation()
        example_5_optimization()
        example_6_class_methods()
        example_7_error_handling()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("\nKey takeaways:")
        print("- Always set FI_API_KEY and FI_SECRET_KEY environment variables")
        print("- Use unique dataset names to avoid conflicts")
        print("- Clean up datasets after use to avoid clutter")
        print("- Handle errors appropriately for robust applications")
        print("- Use class methods for simple one-off operations")
        print("- Use instance methods for complex chained operations")
        
    except MissingAuthError as e:
        print(f"\n✗ Authentication Error: {e}")
        print("Please set your FI_API_KEY and FI_SECRET_KEY environment variables")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


if __name__ == "__main__":
    main() 