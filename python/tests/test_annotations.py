#!/usr/bin/env python3
"""
Comprehensive test script for fi.annotations package.

This script tests all functionality of the annotation client including:
- Project listing
- Label fetching
- Simple DataFrame annotation logging
- Error handling

Usage:
    python test_annotations.py

Configure your credentials and base URL below.
"""

import json
import sys
import time
from typing import List, Dict, Any
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Import the annotation client
try:
    from fi.annotations import Annotation, AnnotationLabel, BulkAnnotationResponse
except ImportError as e:
    print(f"❌ Failed to import fi.annotations: {e}")
    print("Make sure the package is installed: pip install -e .")
    sys.exit(1)

# ────────────────────────────
# ─── CONFIGURATION ─────────
# ────────────────────────────
BASE_URL = "http://localhost:8000"
FI_API_KEY = "3cdedf31ab9046bf9d1936a3d8ac2188"
FI_SECRET_KEY = "9e869a24292e4f2781f330c769eda42b"
TEST_SPAN_ID = "a2675825a82a4208"  # Replace with valid span ID
TEST_PROJECT_NAME = "Agent_Summarization"  # Replace with actual project name

console = Console()


def test_client_initialization():
    """Test 1: Client initialization"""
    console.rule("[bold blue]Test 1: Client Initialization")
    
    try:
        client = Annotation(
            fi_api_key=FI_API_KEY,
            fi_secret_key=FI_SECRET_KEY,
            fi_base_url=BASE_URL
        )
        console.print("✅ Client initialized successfully")
        return client
    except Exception as e:
        console.print(f"❌ Client initialization failed: {e}")
        return None


def test_list_projects(client: Annotation):
    """Test 2: List projects"""
    console.rule("[bold blue]Test 2: List Projects")
    
    try:
        projects = client.list_projects()
        console.print(f"✅ Found {len(projects)} projects")
        
        if projects:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Name")
            table.add_column("ID")
            table.add_column("Type")
            
            for project in projects[:5]:  # Show first 5
                table.add_row(
                    project.name,
                    project.id,
                    project.project_type or "N/A"
                )
            console.print(table)
            return projects[0]  # Return first project for further tests
        else:
            console.print("⚠️ No projects found")
            return None
            
    except Exception as e:
        console.print(f"❌ List projects failed: {e}")
        return None


def test_get_labels(client: Annotation, project_id: str = None):
    """Test 3: Get annotation labels"""
    console.rule("[bold blue]Test 3: Get Annotation Labels")
    
    try:
        labels = client.get_labels(project_id=project_id)
        console.print(f"✅ Found {len(labels)} labels")
        
        if labels:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Name")
            table.add_column("Type") 
            table.add_column("ID")
            
            for label in labels[:5]:  # Show first 5
                table.add_row(label.name, label.type, label.id)
            console.print(table)
            return labels
        else:
            console.print("⚠️ No labels found")
            return []
            
    except Exception as e:
        console.print(f"❌ Get labels failed: {e}")
        return []


def test_simple_annotation_logging(client: Annotation, labels: List[AnnotationLabel]):
    """Test 4: Simple annotation logging with flat DataFrame"""
    console.rule("[bold blue]Test 4: Simple Annotation Logging")
    
    if not labels:
        console.print("⚠️ Skipping - no labels available")
        return
    
    try:
        timestamp = int(time.time())
        
        # Create simple flat DataFrame using actual label names from the project
        df = pd.DataFrame({
            "context.span_id": [TEST_SPAN_ID],
            "annotation.crazy.text": ["Test annotation text"],  # Using 'crazy' text label
            "annotation.crazy.score": [3.5],  # Using 'crazy' numeric label  
            "annotation.notes": [f"Test note {timestamp}"]
        })
        
        console.print("📤 Testing simple annotation logging...")
        console.print("DataFrame structure:")
        rprint(df.to_dict(orient="records")[0])
        
        response = client.log_annotations(df, project_name=TEST_PROJECT_NAME)
        
        console.print("✅ Simple annotation logging successful!")
        console.print(f"  • Annotations created: {response.annotationsCreated}")
        console.print(f"  • Annotations updated: {response.annotationsUpdated}")
        console.print(f"  • Notes created: {response.notesCreated}")
        console.print(f"  • Total succeeded: {response.succeededCount}")
        console.print(f"  • Errors: {response.errorsCount}")
        
        if response.errors:
            console.print("Errors:", response.errors)
        if response.warnings:
            console.print("Warnings:", response.warnings)
            
    except Exception as e:
        console.print(f"❌ Simple annotation logging failed: {e}")


def test_multiple_rows_dataframe(client: Annotation):
    """Test 5: Multiple rows DataFrame"""
    console.rule("[bold blue]Test 5: Multiple Rows DataFrame")
    
    try:
        timestamp = int(time.time())
        
        # Create DataFrame with multiple rows
        df = pd.DataFrame({
            "context.span_id": [TEST_SPAN_ID, TEST_SPAN_ID],
            "annotation.crazy.text": ["Good response", "Bad response"],
            "annotation.crazy.score": [4.5, 2.0],
            "annotation.notes": [f"First note {timestamp}", f"Second note {timestamp}"]
        })
        
        console.print("📤 Testing multiple rows DataFrame...")
        console.print(f"   • {len(df)} rows to process")
        
        response = client.log_annotations(df, project_name=TEST_PROJECT_NAME)
        
        console.print("✅ Multiple rows successful!")
        console.print(f"  • Total succeeded: {response.succeededCount}")
        
    except Exception as e:
        console.print(f"❌ Multiple rows failed: {e}")


def test_empty_dataframe(client: Annotation):
    """Test 6: Empty DataFrame handling"""
    console.rule("[bold blue]Test 6: Empty DataFrame")
    
    try:
        # Create empty DataFrame
        df = pd.DataFrame({
            "context.span_id": [],
            "annotation.crazy.text": [],
            "annotation.notes": []
        })
        
        console.print("📤 Testing empty DataFrame...")
        response = client.log_annotations(df, project_name=TEST_PROJECT_NAME)
        
        console.print("✅ Empty DataFrame handled!")
        console.print(f"  • Total succeeded: {response.succeededCount}")
        
    except Exception as e:
        console.print(f"❌ Empty DataFrame failed: {e}")


def test_invalid_input(client: Annotation):
    """Test 7: Invalid input handling"""
    console.rule("[bold blue]Test 7: Invalid Input Handling")
    
    try:
        # Test with non-DataFrame input
        console.print("📤 Testing invalid input (list instead of DataFrame)...")
        response = client.log_annotations([{"test": "data"}])  # Should fail
        console.print("❌ Should have failed but didn't!")
        
    except ValueError as e:
        console.print(f"✅ Correctly rejected invalid input: {e}")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")


def test_project_scoping(client: Annotation):
    """Test 8: Project scoping validation"""
    console.rule("[bold blue]Test 8: Project Scoping")
    
    try:
        timestamp = int(time.time())
        
        # Test with valid project name
        df = pd.DataFrame({
            "context.span_id": [TEST_SPAN_ID],
            "annotation.crazy.text": ["Project scoped annotation"],
            "annotation.notes": [f"Project test {timestamp}"]
        })
        
        console.print("📤 Testing with valid project name...")
        response = client.log_annotations(df, project_name=TEST_PROJECT_NAME)
        console.print(f"✅ Valid project: {response.succeededCount} succeeded")
        
        # Test with invalid project name
        console.print("📤 Testing with invalid project name...")
        try:
            response = client.log_annotations(df, project_name="NonExistentProject")
            console.print("❌ Should have failed with invalid project!")
        except ValueError as e:
            console.print(f"✅ Correctly rejected invalid project: {e}")
            
        # Test without project name (should work with global labels)
        console.print("📤 Testing without project name...")
        try:
            response = client.log_annotations(df)  # No project_name
            console.print(f"✅ No project specified: {response.succeededCount} succeeded")
        except Exception as e:
            console.print(f"⚠️ No project failed (expected if labels don't exist globally): {e}")
            
    except Exception as e:
        console.print(f"❌ Project scoping test failed: {e}")


def main():
    """Run all tests"""
    console.print("[bold green]🧪 Starting fi.annotations test suite")
    console.print(f"Base URL: {BASE_URL}")
    console.print()
    
    # Test 1: Initialize client
    client = test_client_initialization()
    if not client:
        console.print("[bold red]❌ Cannot continue without client")
        return
    
    # Test 2: List projects
    first_project = test_list_projects(client)
    project_id = first_project.id if first_project else None
    
    # Test 3: Get labels
    labels = test_get_labels(client, project_id)
    
    # Test 4: Simple annotation logging
    test_simple_annotation_logging(client, labels)
    
    # Test 5: Multiple rows
    test_multiple_rows_dataframe(client)
    
    # Test 6: Empty DataFrame
    test_empty_dataframe(client)
    
    # Test 7: Invalid input
    test_invalid_input(client)
    
    # Test 8: Project scoping
    test_project_scoping(client)
    
    console.rule("[bold green]🎉 Test Suite Complete")
    console.print("All tests finished! Check results above for any failures.")


if __name__ == "__main__":
    main() 