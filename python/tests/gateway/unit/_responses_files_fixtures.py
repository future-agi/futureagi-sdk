"""Response and file payload fixtures."""
RESPONSE_OBJECT = {
    "id": "resp-001",
    "object": "response",
    "model": "gpt-4o",
    "created_at": 1700000000,
    "status": "completed",
    "output": [
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Hello, world!"}],
        }
    ],
    "usage": {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    },
    "metadata": {"session": "abc"},
    "error": None,
}


RESPONSE_WITH_TOOLS = {
    "id": "resp-002",
    "object": "response",
    "model": "gpt-4o",
    "created_at": 1700000001,
    "status": "completed",
    "output": [
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Using tools now."}],
        }
    ],
    "usage": {
        "input_tokens": 20,
        "output_tokens": 10,
        "total_tokens": 30,
    },
    "metadata": None,
    "error": None,
}


FILE_OBJECT = {
    "id": "file-abc123",
    "object": "file",
    "bytes": 1024,
    "created_at": 1700000000,
    "filename": "training.jsonl",
    "purpose": "fine-tune",
    "status": "processed",
    "status_details": None,
}


FILE_LIST = {
    "data": [FILE_OBJECT],
    "object": "list",
}


FILE_DELETED = {
    "id": "file-abc123",
    "object": "file",
    "deleted": True,
}
