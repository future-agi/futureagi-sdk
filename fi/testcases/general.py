import json
from typing import Optional

from pydantic import BaseModel


class TestCase(BaseModel):
    text: Optional[str] = None
    document: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    prompt: Optional[str] = None
    criteria: Optional[str] = None
    actual_json: Optional[dict] = None
    expected_json: Optional[dict] = None
    response: Optional[str] = None

    def __post_init__(self):
        if self.actual_json is not None:
            self.actual_json = json.loads(self.actual_json)
        if self.expected_json is not None:
            self.expected_json = json.loads(self.expected_json)
