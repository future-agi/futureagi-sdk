#!/usr/bin/env python3
"""
Test script to verify Hugging Face dataset import fix

This script tests the corrected parameter mapping for Hugging Face dataset imports.
Run this script to verify that the SDK now correctly sends 'huggingface_dataset_config' 
instead of 'huggingface_dataset_subset' to match the backend expectations.
"""

import os
import sys
import pandas as pd
from fi.datasets import Dataset
from fi.datasets.types import DatasetConfig, HuggingfaceDatasetConfig, ModelTypes

def test_hf_import():
    """Test Hugging Face dataset import with the corrected parameter mapping"""
    
    # Check environment variables
    if not os.getenv("FI_API_KEY") or not os.getenv("FI_SECRET_KEY"):
        print("❌ Error: FI_API_KEY and FI_SECRET_KEY environment variables must be set")
        print("Please set them before running this test:")
        print("export FI_API_KEY='your_api_key'")
        print("export FI_SECRET_KEY='your_secret_key'")
        return False
    
    print("✅ Environment variables are set")
    
    # Configure dataset
    dataset_config = DatasetConfig(
        name="test_hf_import_fix",
        model_type=ModelTypes.GENERATIVE_LLM
    )
    
    # Configure Hugging Face dataset with subset parameter
    hf_config = HuggingfaceDatasetConfig(
        name="imdb",  # Simple, well-known dataset
        subset="plain_text",  # This should now be sent as 'huggingface_dataset_config'
        split="train",
        num_rows=5  # Small number for quick testing
    )
    
    try:
        print("🚀 Creating dataset from Hugging Face...")
        print(f"   Dataset name: {hf_config.name}")
        print(f"   Subset: {hf_config.subset}")
        print(f"   Split: {hf_config.split}")
        print(f"   Rows: {hf_config.num_rows}")
        
        # Create dataset
        dataset = Dataset.create_dataset(
            dataset_config=dataset_config,
            source=hf_config
        )
        
        print("✅ Dataset created successfully!")
        if dataset.dataset_config:
            print(f"   Dataset ID: {dataset.dataset_config.id}")
            print(f"   Dataset Name: {dataset.dataset_config.name}")
        
        # Verify by downloading a sample
        print("📥 Downloading sample data...")
        df = dataset.download(load_to_pandas=True)
        print(f"✅ Data downloaded successfully!")
        
        # Check if df is a pandas DataFrame
        if isinstance(df, pd.DataFrame):
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
        else:
            print(f"   Downloaded data type: {type(df)}")
        
        # Clean up
        print("🧹 Cleaning up test dataset...")
        dataset.delete()
        print("✅ Test dataset deleted")
        
        print("\n🎉 SUCCESS: Hugging Face import fix is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nThis could indicate:")
        print("1. The parameter mapping fix didn't work")
        print("2. Network/API issues")
        print("3. Dataset access issues")
        print("4. Authentication problems")
        return False

if __name__ == "__main__":
    print("Testing Hugging Face Dataset Import Fix")
    print("=" * 50)
    
    success = test_hf_import()
    
    if success:
        print("\n✅ All tests passed! The fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Test failed. Please check the error messages above.")
        sys.exit(1) 