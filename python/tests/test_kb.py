import pytest
import os
import time

from fi.kb import KnowledgeBase
from fi.kb import KnowledgeBaseConfig

KB_CLIENT = None
TEST_KB_NAME = "sdk-test-kb-" + str(int(time.time()))
TEST_FILE_1 = 'tests/test_kb_1.txt'
TEST_FILE_2 = 'tests/test_kb_2.txt'
TEST_FILE_3 = 'tests/test_kb_3.txt'

def check_files_exist():
    files = [TEST_FILE_1, TEST_FILE_2, TEST_FILE_3]
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(f"Test files not found: {missing}. Please create these files to run the tests.")

@pytest.fixture(scope="module")
def kb_client():
    """Create a single KB client to use across all tests"""
    global KB_CLIENT
    if KB_CLIENT is None:
        # check_files_exist()
        KB_CLIENT = KnowledgeBase()
    return KB_CLIENT

def test_create_kb(kb_client):
    """Test creating a knowledge base"""
    try:
        kb_client = kb_client.create_kb(
            name=TEST_KB_NAME, 
            file_paths=[TEST_FILE_1, TEST_FILE_3]
        )
        assert kb_client is not None
        assert kb_client.kb is not None
        assert kb_client.kb.id is not None
        assert kb_client.kb.name == TEST_KB_NAME
        assert len(kb_client.kb.files) > 0
        print(f"Created KB: {kb_client.kb.id} with name: {kb_client.kb.name}")
    except Exception as e:
        pytest.fail(f"Failed to create KB: {str(e)}")

def test_update_kb(kb_client):
    """Test updating a knowledge base"""
    try:
        if not kb_client or not kb_client.kb or not kb_client.kb.id:
            pytest.skip("KB not created, skipping update test")
            
        original_files_count = len(kb_client.kb.files) if kb_client.kb.files else 0
        print(f"Original files count: {original_files_count}")
        
        kb_client = kb_client.update_kb(file_paths=[TEST_FILE_2])
        
        assert kb_client is not None
        assert kb_client.kb is not None
        assert kb_client.kb.id is not None
        assert hasattr(kb_client.kb, 'files')
        print(f"Updated KB: {kb_client.kb.id} with name: {kb_client.kb.name}, files: {len(kb_client.kb.files)}")
    except Exception as e:
        pytest.fail(f"Failed to update KB: {str(e)}")

def test_delete_files_from_kb(kb_client):
    """Test deleting files from a knowledge base"""
    try:
        if not kb_client or not kb_client.kb or not kb_client.kb.id:
            pytest.skip("KB not created, skipping delete files test")
        
        file_names = ["file_3.txt"]
        kb_client = kb_client.delete_files_from_kb(file_names=file_names)
        
        assert kb_client is not None
        assert kb_client.kb is not None
        print(f"Deleted file, remaining files: {len(kb_client.kb.files)}")
    except Exception as e:
        pytest.fail(f"Failed to delete files: {str(e)}")

def test_delete_kb(kb_client):
    """Test deleting a knowledge base"""
    try:
        if not kb_client or not kb_client.kb or not kb_client.kb.id:
            pytest.skip("KB not created, skipping delete KB test")
            
        kb_id = kb_client.kb.id
        print(f"Deleting KB: {kb_id}")
        
        kb_client = kb_client.delete_kb(kb_ids=[kb_id])
        
        assert kb_client is not None
        assert kb_client.kb is None
        print(f"Successfully deleted KB: {kb_id}")
    except Exception as e:
        pytest.fail(f"Failed to delete KB: {str(e)}")