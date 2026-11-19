from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, Field

from fi._compat_fields import LegacyFieldsModel as _LegacyFieldsModel, legacy_property as _legacy_property


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


class BulkAnnotationResponse(_LegacyFieldsModel):
    """Bulk annotation success, accepting both published and server spellings.

    The published 0.7.0 snake_case names remain the model fields and serialization
    keys, including when by_alias=True. Older camelCase inputs and read/write
    properties emit one DeprecationWarning per alias per process.
    Unknown fields continue to be ignored.
    """

    message: str
    annotations_created: int = Field(validation_alias=AliasChoices("annotations_created", "annotationsCreated"))
    annotations_updated: int = Field(validation_alias=AliasChoices("annotations_updated", "annotationsUpdated"))
    notes_created: int = Field(validation_alias=AliasChoices("notes_created", "notesCreated"))
    succeeded_count: int = Field(validation_alias=AliasChoices("succeeded_count", "succeededCount"))
    errors_count: int = Field(validation_alias=AliasChoices("errors_count", "errorsCount"))
    warnings_count: int = Field(validation_alias=AliasChoices("warnings_count", "warningsCount"))
    warnings: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None

    annotationsCreated = _legacy_property("annotationsCreated", "annotations_created")
    annotationsUpdated = _legacy_property("annotationsUpdated", "annotations_updated")
    errorsCount = _legacy_property("errorsCount", "errors_count")
    notesCreated = _legacy_property("notesCreated", "notes_created")
    succeededCount = _legacy_property("succeededCount", "succeeded_count")
    warningsCount = _legacy_property("warningsCount", "warnings_count")
