from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import pandas as pd
from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.annotations.types import AnnotationLabel, BulkAnnotationResponse, Project
from fi.utils.errors import InvalidAuthError, SDKException
from fi.utils.logging import logger
from fi.utils.routes import Routes


class _AnnotationResponseHandler(ResponseHandler[Dict[str, Any], BulkAnnotationResponse]):
    """Handle responses for annotation related requests."""

    @classmethod
    def _parse_success(cls, response: Response) -> Union[Dict[str, Any], BulkAnnotationResponse]:
        data = response.json()

        # Backend often wraps the payload in {'status': True, 'result': {...}}
        if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict):
            data = data["result"]

        # Attempt to build strongly-typed response; fall back to raw dict on failure
        try:
            return BulkAnnotationResponse(**data)
        except Exception:
            return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        else:
            try:
                detail = response.json()
                raise SDKException(detail.get("message", response.text))
            except Exception:
                response.raise_for_status()


class _AnnotationLabelsResponseHandler(ResponseHandler[List[Dict[str, Any]], List[AnnotationLabel]]):
    """Parses /tracer/get-annotation-labels/ response into list of AnnotationLabel."""

    @classmethod
    def _parse_success(cls, response: Response) -> List[AnnotationLabel]:
        data = response.json()
        if isinstance(data, dict) and 'result' in data:
            data = data['result']
        # Expecting list of labels
        try:
            return [AnnotationLabel(**item) for item in data]  # type: ignore[arg-type]
        except Exception:  # malformed? return raw
            return data  # type: ignore[return-value]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        else:
            response.raise_for_status()


class _ProjectsResponseHandler(ResponseHandler[List[Dict[str, Any]], List[Project]]):
    """Parses /tracer/project/list_projects/ response into list of Project."""

    @classmethod
    def _parse_success(cls, response: Response) -> List[Project]:
        data = response.json()
        
        # Handle wrapped response with metadata
        if isinstance(data, dict) and 'result' in data:
            # Response format: {"result": {"table": [...], "metadata": {...}}}
            result_data = data['result']
            if isinstance(result_data, dict) and 'table' in result_data:
                projects_data = result_data['table']
            else:
                projects_data = result_data
        else:
            projects_data = data
        
        try:
            return [Project(**project) for project in projects_data]
        except Exception:
            return projects_data  # type: ignore[return-value]

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        else:
            response.raise_for_status()


class Annotation(APIKeyAuth):
    """SDK client for logging human annotations using flat DataFrame format."""

    def __init__(self, fi_api_key: Optional[str] = None, 
                 fi_secret_key: Optional[str] = None, 
                 fi_base_url: Optional[str] = None, **kwargs):
        super().__init__(fi_api_key, fi_secret_key, fi_base_url, **kwargs)

    def log_annotations(
        self,
        dataframe: pd.DataFrame,
        *,
        project_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> BulkAnnotationResponse:
        """Log annotations using flat DataFrame format.
        
        Expected DataFrame columns:
        - context.span_id: Span ID for the annotation
        - annotation.{name}.text: Text annotations
        - annotation.{name}.label: Categorical annotations  
        - annotation.{name}.score: Numeric annotations
        - annotation.{name}.rating: Star ratings (1-5)
        - annotation.{name}.thumbs: Thumbs up/down (True/False)
        - annotation.notes: Optional notes text
        
        Args:
            dataframe: DataFrame with flat annotation format
            project_name: Project name to resolve annotation names within project scope
            timeout: Request timeout
        
        Example:
            df = pd.DataFrame({
                "context.span_id": ["span123"],
                "annotation.quality.text": ["good response"], 
                "annotation.category.label": ["helpful"],
                "annotation.rating.rating": [4],
                "annotation.sentiment.score": [4.5],
                "annotation.helpful.thumbs": [True],
                "annotation.notes": ["Great response!"]
            })
            
            client.log_annotations(df, project_name="My Project")
        """
        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Convert flat DataFrame to nested records format expected by backend
        records = self._convert_dataframe_to_records(dataframe, project_name)
        
        logger.info("Sending %s annotation records via bulk endpoint", len(records))

        config = RequestConfig(
            method=HttpMethod.POST,
            url=f"{self._base_url}/{Routes.bulk_annotation.value}",
            json={"records": records},
            timeout=timeout,
        )

        response = self.request(config, _AnnotationResponseHandler)

        if isinstance(response, BulkAnnotationResponse):
            return response

        try:
            return BulkAnnotationResponse(**response)  # type: ignore[arg-type]
        except Exception as exc:
            raise SDKException("Bulk annotation response could not be parsed") from exc

    def _convert_dataframe_to_records(self, df: pd.DataFrame, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Convert flat DataFrame to nested records format."""
        records = []
        
        for _, row in df.iterrows():
            span_id = row.get("context.span_id")
            if pd.isna(span_id):
                continue
                
            record = {
                "observation_span_id": span_id,
                "annotations": [],
                "notes": []
            }
            
            # Process annotation columns
            for col in df.columns:
                if col.startswith("annotation.") and not col.endswith(".notes"):
                    value = row[col]
                    if pd.notna(value):
                        annotation = self._parse_annotation_column(col, value, project_name)
                        if annotation:
                            record["annotations"].append(annotation)
            
            # Process notes
            if "annotation.notes" in df.columns:
                notes_value = row["annotation.notes"]
                if pd.notna(notes_value):
                    record["notes"].append({"text": str(notes_value)})
            
            if record["annotations"] or record["notes"]:
                records.append(record)
        
        return records

    def _parse_annotation_column(self, column: str, value: Any, project_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Parse annotation column name and value into annotation dict."""
        # Format: annotation.{name}.{type}
        parts = column.split(".")
        if len(parts) != 3:
            return None
            
        _, name, value_type = parts
        
        # Get project-specific label ID
        label_id = self._get_label_id_for_name_and_type(name, value_type, project_name)
        if not label_id:
            raise ValueError(f"No annotation label found for name '{name}' and type '{value_type}' in project '{project_name}'")
        
        # Map column types to backend fields
        if value_type == "text":
            return {
                "annotation_label_id": label_id,
                "value": str(value)
            }
        elif value_type == "label":
            return {
                "annotation_label_id": label_id,
                "value_str_list": [str(value)] if not isinstance(value, list) else [str(v) for v in value]
            }
        elif value_type == "score":
            return {
                "annotation_label_id": label_id, 
                "value_float": float(value)
            }
        elif value_type == "rating":
            return {
                "annotation_label_id": label_id,
                "value_float": float(value)
            }
        elif value_type == "thumbs":
            return {
                "annotation_label_id": label_id,
                "value_bool": bool(value)
            }
        
        return None

    def _get_project_id(self, project_name: str) -> str:
        """Get project ID by name. Raises ValueError if not found or ambiguous."""
        projects = self.list_projects(name=project_name)
        if not projects:
            raise ValueError(f"Project '{project_name}' not found")
        if len(projects) > 1:
            project_list = [f"{p.name} (id: {p.id})" for p in projects]
            raise ValueError(f"Multiple projects found for '{project_name}': {project_list}")
        return projects[0].id

    def _get_label_id_for_name_and_type(self, name: str, column_type: str, project_name: Optional[str] = None) -> Optional[str]:
        """Get label ID for annotation name and column type, optionally filtered by project."""
        # Get project ID if project name provided
        project_id = None
        if project_name:
            project_id = self._get_project_id(project_name)
        
        # Get labels (filtered by project if specified)
        labels = self.get_labels(project_id=project_id)
        
        # Map column types to backend label types
        type_mapping = {
            "text": "text",
            "label": "categorical", 
            "score": "numeric",
            "rating": "star",
            "thumbs": "thumbs_up_down"
        }
        
        expected_label_type = type_mapping.get(column_type)
        if not expected_label_type:
            return None
        
        # Find matching label
        for label in labels:
            if label.name == name and label.type.lower() == expected_label_type:
                return label.id
        
        return None

    def get_labels(
        self,
        *,
        project_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[AnnotationLabel]:
        """Fetch annotation labels available to the user."""
        params: Dict[str, Any] = {}
        if project_id:
            params["project_id"] = project_id

        config = RequestConfig(
            method=HttpMethod.GET,
            url=f"{self._base_url}/{Routes.get_annotation_labels.value}",
            params=params,
            timeout=timeout,
        )
        return self.request(config, _AnnotationLabelsResponseHandler)

    def list_projects(
        self,
        *,
        project_type: Optional[str] = None,
        name: Optional[str] = None,
        page_number: int = 0,
        page_size: int = 20,
        timeout: Optional[int] = None,
    ) -> List[Project]:
        """List available projects."""
        params: Dict[str, Any] = {
            "page_number": page_number,
            "page_size": page_size,
        }
        if project_type:
            params["project_type"] = project_type
        if name:
            params["name"] = name

        config = RequestConfig(
            method=HttpMethod.GET,
            url=f"{self._base_url}/{Routes.list_projects.value}",
            params=params,
            timeout=timeout,
        )
        return self.request(config, _ProjectsResponseHandler) 