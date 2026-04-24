from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Project(BaseModel):
    """Represents a project returned by /tracer/project/list_projects/."""
    
    id: str
    name: str
    project_type: Optional[str] = None
    created_at: Optional[str] = None
    # Add other fields as needed based on actual API response


class AnnotationLabel(BaseModel):
    """Represents an annotation label definition returned by 
    /tracer/get-annotation-labels/ endpoint.
    """

    id: str
    name: str
    type: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class BulkAnnotationResponse(BaseModel):
    """Represents the success payload from bulk-annotation endpoint."""

    message: str
    annotations_created: int
    annotations_updated: int
    notes_created: int
    succeeded_count: int
    errors_count: int
    warnings_count: int
    warnings: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None
