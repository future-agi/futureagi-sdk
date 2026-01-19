from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel
import uuid

from typing import List, Dict

class StatusType(Enum):
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    PARTIAL_COMPLETED = "PartialCompleted"
    FAILED = "Failed"

class KnowledgeBaseConfig(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    status: str = StatusType.PROCESSING.value
    last_error: Optional[str] = None
    files: List[str] = []