import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from fi.utils.types import ModelTypes


class DataTypeChoices(str, Enum):
    """Valid data types for dataset columns"""

    TEXT = "text"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    JSON = "json"
    ARRAY = "array"
    IMAGE = "image"
    DATETIME = "datetime"

    @classmethod
    def get_python_type(cls, data_type: "DataTypeChoices") -> type:
        """Get the corresponding Python type for a data type"""
        TYPE_MAPPING = {
            cls.TEXT: str,
            cls.BOOLEAN: bool,
            cls.INTEGER: int,
            cls.FLOAT: float,
            cls.JSON: dict,
            cls.ARRAY: list,
            cls.IMAGE: str,
            cls.DATETIME: datetime,
        }
        return TYPE_MAPPING.get(data_type, str)


class SourceChoices(str, Enum):
    """Valid source types for dataset columns"""

    EVALUATION = "evaluation"
    RUN_PROMPT = "run_prompt"
    EXPERIMENT = "experiment"
    OPTIMISATION = "optimisation"
    EXPERIMENT_EVALUATION = "experiment_evaluation"
    OPTIMISATION_EVALUATION = "optimisation_evaluation"
    EXTRACTED_JSON = "extracted_json"
    CLASSIFICATION = "classification"
    EXTRACTED_ENTITIES = "extracted_entities"
    API_CALL = "api_call"
    PYTHON_CODE = "python_code"
    VECTOR_DB = "vector_db"
    CONDITIONAL = "conditional"
    OTHERS = "OTHERS"

    @classmethod
    def get_choices(cls) -> List[tuple[str, str]]:
        """Get list of choices in (value, display_name) format"""
        return [(tag.value, tag.name.replace("_", " ").title()) for tag in cls]


class Column(BaseModel):
    """Column information for dataset tables"""

    id: uuid.UUID
    name: str
    data_type: DataTypeChoices
    source: SourceChoices
    source_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_frozen: bool = False
    is_visible: bool = True
    eval_tags: List[str] = Field(default_factory=list)
    average_score: Optional[float] = None
    order_index: int = 0

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate column name"""
        if not v.strip():
            raise ValueError("Column name cannot be empty")
        if len(v) > 255:
            raise ValueError("Column name too long (max 255 characters)")
        return v.strip()

    class Config:
        frozen = True


class Cell(BaseModel):
    """Cell information for dataset tables"""

    column_id: uuid.UUID
    row_id: uuid.UUID
    value: Optional[str] = None
    value_infos: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: Optional[str] = None
    failure_reason: Optional[str] = None

    @field_validator("value")
    def validate_value(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate cell value"""
        if v is not None and len(str(v)) > 65535:
            raise ValueError("Cell value too long (max 65535 characters)")
        return v

    @field_validator("value_infos")
    def validate_value_infos(
        cls, v: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Validate value_infos structure"""
        if v is None:
            return []
        return v

    class Config:
        frozen = True


class Row(BaseModel):
    """Row information for dataset tables"""

    id: uuid.UUID
    order: int
    cells: List[Cell]

    @field_validator("order")
    def validate_order(cls, v: int) -> int:
        """Validate row order"""
        if v < 0:
            raise ValueError("Row order must be non-negative")
        return v

    @field_validator("cells")
    def validate_cells(cls, v: List[Cell]) -> List[Cell]:
        """Validate cells list"""
        if not v:
            raise ValueError("Row must have at least one cell")
        return v

    class Config:
        frozen = True


class DatasetConfig(BaseModel):
    """Dataset response model"""

    id: Optional[uuid.UUID] = None
    name: str
    model_type: ModelTypes
    column_order: Optional[List[str]] = Field(default_factory=list)
    column_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Validate dataset name"""
        if not v.strip():
            raise ValueError("Dataset name cannot be empty")
        if len(v) > 255:
            raise ValueError("Dataset name too long (max 255 characters)")
        return v.strip()

    @field_validator("column_order")
    def validate_column_order(cls, v: List[str]) -> List[str]:
        """Validate that column_order contains valid UUIDs"""
        try:
            return [str(uuid.UUID(col_id)) for col_id in v]
        except ValueError as e:
            raise ValueError(f"Invalid UUID in column_order: {e}")


class HuggingfaceDatasetConfig(BaseModel):
    """Hugging Face dataset configuration"""

    name: str = Field(..., description="Name of the Hugging Face dataset")
    subset: Optional[str] = "default"
    split: Optional[str] = "train"
    num_rows: Optional[int] = None


class DatasetTable(BaseModel):
    """Dataset table response model"""

    id: uuid.UUID
    columns: List[Column]
    rows: List[Row]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    dataset_config: Optional[DatasetConfig] = None

    def to_df(self) -> pd.DataFrame:
        """Convert dataset table to pandas DataFrame with proper data types"""
        try:
            # Create a dictionary to store column data with proper types
            data = {col.name: [] for col in self.columns}
            column_types = {col.name: col.data_type for col in self.columns}

            # Process each row
            for row in self.rows:
                for cell in row.cells:
                    # Find the corresponding column
                    try:
                        col = next(c for c in self.columns if c.id == cell.column_id)
                    except StopIteration:
                        raise ValueError(f"Column not found for cell {cell.id}")

                    value = cell.value
                    if value is not None:
                        value = self._convert_value(value, column_types[col.name])
                    data[col.name].append(value)

            df = pd.DataFrame(data)
            return self._set_column_types(df, column_types)
        except Exception as e:
            raise ValueError(f"Error converting to DataFrame: {str(e)}")

    def _convert_value(self, value: str, data_type: DataTypeChoices) -> Any:
        """Convert string value to appropriate type"""
        try:
            if data_type == DataTypeChoices.FLOAT:
                return float(value)
            elif data_type == DataTypeChoices.BOOLEAN:
                return value.lower() == "true"
            elif data_type == DataTypeChoices.DATETIME:
                return pd.to_datetime(value)
            elif data_type == DataTypeChoices.JSON:
                return pd.read_json(value)
            elif data_type == DataTypeChoices.ARRAY:
                return value.split(",")
            return value
        except (ValueError, TypeError):
            return None

    def _set_column_types(
        self, df: pd.DataFrame, column_types: Dict[str, DataTypeChoices]
    ) -> pd.DataFrame:
        """Set appropriate pandas dtypes for columns"""
        for col_name, data_type in column_types.items():
            if data_type == DataTypeChoices.FLOAT:
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
            elif data_type == DataTypeChoices.BOOLEAN:
                df[col_name] = df[col_name].astype("boolean")
            elif data_type == DataTypeChoices.DATETIME:
                df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
        return df

    def to_json(self, file_path: str) -> str:
        """Convert dataset table to JSON string"""
        df = self.to_df()
        if file_path and os.path.exists(file_path):
            df.to_json(file_path, orient="records", lines=True, mode="a")
        elif file_path and not os.path.exists(file_path):
            df.to_json(file_path, orient="records", lines=True)

    def to_csv(self, file_path: str) -> str:
        """Convert dataset table to CSV string"""
        df = self.to_df()
        if file_path and os.path.exists(file_path):
            df.to_csv(file_path, mode="a", index=False)
        elif file_path and not os.path.exists(file_path):
            df.to_csv(file_path, index=False)
        return file_path

    def to_excel(self, file_path: str) -> str:
        """Convert dataset table to Excel file"""
        df = self.to_df()
        if file_path and os.path.exists(file_path):
            df.to_excel(file_path, mode="a", index=False)
        elif file_path and not os.path.exists(file_path):
            df.to_excel(file_path, index=False)
        return file_path

    def to_file(self, file_path: str) -> str:
        """Convert dataset table to file"""
        if file_path.endswith(".json"):
            return self.to_json(file_path)
        elif file_path.endswith(".csv"):
            return self.to_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            return self.to_excel(file_path)
        raise ValueError(f"Unsupported file format: {file_path}")
