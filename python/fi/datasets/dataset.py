import os
import re
from typing import Any, Dict, List, Optional, Union
import time
import logging
from urllib.parse import urlparse

import pandas as pd
from requests import Response
from requests.exceptions import ConnectionError, Timeout
from tqdm import tqdm

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.datasets.types import (
    Cell,
    Column,
    DatasetConfig,
    DatasetTable,
    HuggingfaceDatasetConfig,
    Row,
)
try :
    from fi.evals.evaluator import EvalInfoResponseHandler
    from fi.evals.templates import EvalTemplate
except ImportError:
    logging.warning(f"ai-evaluation is not installed. Please install it to add evaluations to your dataset.")

from fi.utils.constants import (
    DATASET_TEMP_FILE_PREFIX,
    DATASET_TEMP_FILE_SUFFIX,
    PAGE_SIZE,
)
from fi.utils.errors import (
    InvalidAuthError, 
    DatasetNotFoundError, 
    DatasetError, 
    DatasetAuthError, 
    DatasetValidationError, 
    RateLimitError, 
    ServerError, 
    ServiceUnavailableError,
    UnexpectedDataFormatError
)
from fi.utils.routes import Routes
from fi.utils.utils import get_tempfile_path, get_keys_from_env, get_base_url_from_env

DEFAULT_API_TIMEOUT = 30  # seconds


class LRUCache:
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache: Dict[Any, Any] = {}
        self.access_order: List[Any] = []

    def get(self, key: Any) -> Optional[Any]:
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.capacity:
            if self.access_order:
                oldest = self.access_order.pop(0)
                if oldest in self.cache:
                    del self.cache[oldest]
            
        self.cache[key] = value
        self.access_order.append(key)


class DatasetResponseHandler(ResponseHandler[DatasetConfig, DatasetTable]):
    """Handles responses for dataset requests"""

    @classmethod
    def _parse_dataset_creation(cls, data: Dict[str, Any]) -> DatasetConfig:
        """Parses the response from dataset creation endpoints."""
        return DatasetConfig(
            id=data["result"]["datasetId"],
            name=data["result"]["datasetName"],
            model_type=data["result"]["datasetModelType"],
        )

    @classmethod
    def _parse_dataset_names(cls, data: Dict[str, Any]) -> DatasetConfig:
        """Parses the response from the get-datasets-names endpoint."""
        datasets = data["result"]["datasets"]
        if not datasets:
            raise DatasetNotFoundError("No dataset found matching the criteria.")
        if len(datasets) > 1:
            raise ValueError("Multiple datasets found. Please specify a dataset name.")
        return DatasetConfig(
            id=datasets[0]["datasetId"],
            name=datasets[0]["name"],
            model_type=datasets[0]["modelType"],
        )

    @classmethod
    def _parse_dataset_table(cls, data: Dict[str, Any], response: Response) -> DatasetTable:
        """Parses the response from the get-dataset-table endpoint."""
        try:
            # Extract ID from a URL like: /model-hub/develops/{id}/get-dataset-table/
            path_parts = urlparse(response.url).path.strip('/').split('/')
            id_index = path_parts.index('develops') + 1
            dataset_id = path_parts[id_index]
        except (ValueError, IndexError):
            raise DatasetError(f"Could not parse dataset ID from URL: {response.url}")

        columns = [
            Column(
                id=column["id"],
                name=column["name"],
                data_type=column["dataType"],
                source=column["originType"],
                source_id=column["sourceId"],
                is_frozen=(
                    column["isFrozen"]["isFrozen"]
                    if column["isFrozen"] is not None
                    else False
                ),
                is_visible=column["isVisible"],
                eval_tags=column["evalTag"],
                average_score=column["averageScore"],
                order_index=column["orderIndex"],
            )
            for column in data["result"]["columnConfig"]
        ]
        rows = []
        for row in data["result"]["table"]:
            cells = []
            row_id = row.pop("rowId")
            order = row.pop("order")
            for column_id, value in row.items():
                cells.append(
                    Cell(
                        column_id=column_id,
                        row_id=row_id,
                        value=value.get("cellValue"),
                        value_infos=(
                            [value.get("valueInfos")]
                            if value.get("valueInfos")
                            else None
                        ),
                        metadata=value.get("metadata"),
                        status=value.get("status"),
                        failure_reason=value.get("failureReason"),
                    )
                )
            rows.append(Row(id=row_id, order=order, cells=cells))
        metadata = data["result"]["metadata"]
        return DatasetTable(id=dataset_id, columns=columns, rows=rows, metadata=metadata)

    @classmethod
    def _parse_success(cls, response: Response) -> Union[DatasetConfig, DatasetTable]:
        """Parse successful response into DatasetResponse"""
        data = response.json()
        parsed_path = urlparse(response.url).path

        if parsed_path.endswith(Routes.dataset_names.value):
            return cls._parse_dataset_names(data)

        if Routes.dataset_table.value.split("/")[-2] in parsed_path:
            return cls._parse_dataset_table(data, response)

        creation_routes = [
            Routes.dataset_empty.value,
            Routes.dataset_local.value,
            Routes.dataset_huggingface.value,
        ]
        if any(parsed_path.endswith(route) for route in creation_routes):
            return cls._parse_dataset_creation(data)

        return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        """Comprehensive error handling based on HTTP status codes."""
        error_map = {
            400: DatasetValidationError,
            401: DatasetAuthError,  # Typically for missing or malformed credentials
            403: InvalidAuthError,  # Typically for valid credentials but insufficient permissions
            404: DatasetNotFoundError,
            429: RateLimitError,
            500: ServerError,
            503: ServiceUnavailableError,
        }

        error_cls = error_map.get(response.status_code, DatasetError)
        
        if 500 < response.status_code < 600 and error_cls == DatasetError:
            error_cls = ServerError

        try:
            error_data = response.json()
            message = (
                error_data.get("detail")
                or error_data.get("message")
                or error_data.get("error")
                or str(error_data)
            )
        except ValueError:
            message = response.text or f"HTTP error {response.status_code} with no descriptive message."

        raise error_cls(message)


class Dataset(APIKeyAuth):
    """Manager class for handling datasets

    This client can be used in two ways:
    1. As class methods for simple one-off operations:
        DatasetClient.download_dataset("my_dataset")

    2. As an instance for chained operations:
        client = DatasetClient(dataset_config=config)
        client.create().download("output.csv").delete()
    """

    _dataset_instance_cache = LRUCache(capacity=100)
    __static_attributes__ = ["get_dataset_config"]


    def __init__(
        self,
        dataset_config: Optional[DatasetConfig] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
            **kwargs,
        )

        self.file_path: Optional[str] = None
        if dataset_config and not dataset_config.id:
            try:
                fetched_config = self._fetch_dataset_config(dataset_config.name)
                self.dataset_config = fetched_config
            except DatasetNotFoundError:

                self.dataset_config = dataset_config
            except DatasetError as e:
                raise DatasetError(f"Failed to initialize dataset configuration for {dataset_config.name}: {e}")
        elif dataset_config and dataset_config.id:
            self.dataset_config = dataset_config
        else:
            self.dataset_config = None 

    # Instance methods for chaining
    def create(
        self, source: Optional[Union[str, HuggingfaceDatasetConfig]] = None
    ) -> "Dataset":
        """Create a dataset and return self for chaining"""
        if not self.dataset_config:
            raise DatasetError("dataset_config must be set before creating a dataset.")

        if self.dataset_config.id:
            raise DatasetError(f"Dataset '{self.dataset_config.name}' appears to already exist with ID: {self.dataset_config.id}.")

        response_config = self._create_dataset(self.dataset_config, source)
        self.dataset_config.id = response_config.id
        self.dataset_config.name = response_config.name
        self.dataset_config.model_type = response_config.model_type
        return self

    def download(
        self, file_path: Optional[str] = None, load_to_pandas: bool = False
    ) -> Union[str, pd.DataFrame, "Dataset"]:
        
        if not self.dataset_config or not self.dataset_config.name:
            raise DatasetError("Dataset name must be configured to download.")
        if not self.dataset_config.id:
            raise DatasetError(f"Dataset '{self.dataset_config.name}' must have an ID to be downloaded. Fetch config first if ID is missing.")

        download_result = self._download_dataset(
            self.dataset_config.name, file_path, load_to_pandas
        )
        if load_to_pandas:
            return download_result  
        else:
            self.file_path = download_result
            return self

    def delete(self) -> None:
        """Delete the current dataset"""
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset ID must be configured to delete.")
        self._delete()
        original_name = self.dataset_config.name # type: ignore
        original_model_type = self.dataset_config.model_type # type: ignore
        self.dataset_config = None

    def get_config(self) -> DatasetConfig:
        """Get the current dataset configuration"""
        if not self.dataset_config:
            raise DatasetError("No dataset configured for this instance.")
        return self.dataset_config

    def add_columns(
        self,
        columns: List[Union[Column, dict]],
    ) -> "Dataset":
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to add columns.")

        if not columns:
            raise DatasetValidationError("Columns list cannot be empty.")

        processed_columns: List[Column]
        if all(isinstance(column, dict) for column in columns):
            try:
                processed_columns = [
                    Column(name=column["name"], data_type=column["data_type"])
                    for column in columns 
                ]
            except KeyError as e:
                raise DatasetValidationError(f"Invalid column dictionary structure: Missing key {e}")
            except Exception as e:
                raise DatasetValidationError(f"Invalid column data: {e}")
        elif all(isinstance(column, Column) for column in columns):
            processed_columns = columns 
        else:
            raise DatasetValidationError("Columns must be a list of Column objects or a list of dictionaries.")
        
        self._add_columns(columns=processed_columns)
        return self

    def add_rows(
        self,
        rows: List[Union[Row, dict]],
    ) -> "Dataset":
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to add rows.")

        if not rows:
            raise DatasetValidationError("Rows list cannot be empty.")

        processed_rows: List[Row]
        if all(isinstance(row, dict) for row in rows):
            try:
                processed_rows = [
                    Row(
                        cells=[
                            Cell(column_name=cell["column_name"], value=cell["value"])
                            for cell in row_dict.get("cells", [])
                        ]
                    )
                    for row_dict in rows
                ]
            except KeyError as e:
                raise DatasetValidationError(f"Invalid row dictionary structure: Missing key {e}")
            except Exception as e:
                raise DatasetValidationError(f"Invalid row data: {e}")

        elif all(isinstance(row, Row) for row in rows):
            processed_rows = rows # type: ignore
        else:
            raise DatasetValidationError("Rows must be a list of Row objects or a list of dictionaries.")

        self._add_rows(processed_rows)
        return self

    def get_column_id(self, column_name: str) -> Optional[str]:
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to get a column ID.")
        if not column_name:
            raise DatasetValidationError("Column name cannot be empty.")

        url = f"{self._base_url}/{Routes.dataset_table.value.format(dataset_id=str(self.dataset_config.id))}"
        dataset_table = self.request_with_retry(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=url,
                params={"page_size": 1, "current_page_index": 0},
                timeout=DEFAULT_API_TIMEOUT,
            ),
            response_handler=DatasetResponseHandler,
        )

        for column in dataset_table.columns:
            if column.name == column_name:
                return str(column.id)
        return None

    def add_run_prompt(
        self,
        name: str,
        model: str,
        messages: List[Dict[str, str]],
        output_format: str = "string",
        concurrency: int = 5,
        max_tokens: int = 500,
        temperature: float = 0.5,
        presence_penalty: float = 1,
        frequency_penalty: float = 1,
        top_p: float = 1,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict] = None,
    ) -> "Dataset":

        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to add a run prompt column.")
        if not name:
            raise DatasetValidationError("Run prompt column name cannot be empty.")
        if not model:
            raise DatasetValidationError("Model cannot be empty for run prompt.")
        if not messages:
            raise DatasetValidationError("Messages list cannot be empty for run prompt.")
        for msg in messages:
            if not isinstance(msg, dict):
                raise UnexpectedDataFormatError("Each message must be a dictionary.")
            if "role" not in msg or "content" not in msg:
                raise UnexpectedDataFormatError("Each message must have 'role' and 'content' fields.")

        processed_messages = []
        referenced_columns = set()

        for msg in messages:
            if "role" not in msg:
                msg["role"] = "user"

            if "content" in msg:
                content = msg["content"]
                
                # Convert string content to the expected list format
                if isinstance(content, str):
                    # Handle column references in string content
                    column_refs = re.findall(r"\{\{(.*?)\}\}", content)
                    for col_name in column_refs:
                        col_id = self.get_column_id(col_name)
                        if not col_id:
                            raise DatasetError(
                                f"Referenced column '{{{{{col_name}}}}}' not found in dataset '{self.dataset_config.name}'"
                            )
                        referenced_columns.add(col_name)
                        content = content.replace(
                            f"{{{{{col_name}}}}}", f"{{{{{col_id}}}}}"
                        )
                    
                    # Convert to expected format: list of dictionaries
                    msg["content"] = [{"type": "text", "text": content}]
                    
                elif isinstance(content, list):
                    # Handle list content (already in expected format)
                    processed_content = []
                    for content_item in content:
                        if isinstance(content_item, dict):
                            # Handle column references in dict content
                            if "text" in content_item:
                                text_content = content_item["text"]
                                column_refs = re.findall(r"\{\{(.*?)\}\}", text_content)
                                for col_name in column_refs:
                                    col_id = self.get_column_id(col_name)
                                    if not col_id:
                                        raise DatasetError(
                                            f"Referenced column '{{{{{col_name}}}}}' not found in dataset '{self.dataset_config.name}'"
                                        )
                                    referenced_columns.add(col_name)
                                    text_content = text_content.replace(
                                        f"{{{{{col_name}}}}}", f"{{{{{col_id}}}}}"
                                    )
                                content_item["text"] = text_content
                            processed_content.append(content_item)
                        else:
                            # If list item is not a dict, treat as text
                            processed_content.append({"type": "text", "text": str(content_item)})
                    msg["content"] = processed_content

            processed_messages.append(msg)

        config = {
            "dataset_id": str(self.dataset_config.id),
            "name": name,
            "config": {
                "model": model,
                "output_format": output_format,
                "concurrency": concurrency,
                "messages": processed_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "top_p": top_p,
            },
        }

        if tools:
            config["config"]["tools"] = tools
        if tool_choice is not None:
            config["config"]["tool_choice"] = tool_choice
        if response_format:
            config["config"]["response_format"] = response_format

        url = f"{self._base_url}/{Routes.dataset_add_run_prompt_column.value}"
        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=config, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )
        

        return self

    def add_evaluation(
        self,
        name: str,
        eval_template: str,
        required_keys_to_column_names: Dict[str, str],
        model: str,
        save_as_template: bool = False,
        run: bool = True,
        reason_column: bool = False,
        config: Optional[Dict[str, Any]] = None,
        error_localizer: bool = False,
        kb_id: Optional[str] = None
        ) -> "Dataset":
        try :
            from fi.evals.evaluator import EvalInfoResponseHandler
            from fi.evals.templates import EvalTemplate
        except ImportError:
            raise DatasetError("ai-evaluation is not installed. Please install it to add evaluations to your dataset.")

        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to add an evaluation.")
        if not name:
            raise DatasetValidationError("Evaluation name cannot be empty.")
        if not eval_template:
            raise DatasetValidationError("Evaluation template name cannot be empty.")
        if not required_keys_to_column_names:
            raise DatasetValidationError("required_keys_to_column_names mapping cannot be empty.")

        template_classes = {cls.__name__: cls for cls in EvalTemplate.__subclasses__()}
        if eval_template not in template_classes:
            raise DatasetValidationError(f"Unknown or unsupported template name: {eval_template}")
        
        if not model:
            raise DatasetValidationError("Model cannot be empty for evaluation.")

        eval_id = template_classes[eval_template].eval_id

        url = f"{self._base_url}/sdk/api/v1/eval/{eval_id}/"
        template_details = self.request_with_retry(
            config=RequestConfig(method=HttpMethod.GET, url=url, timeout=DEFAULT_API_TIMEOUT),
            response_handler=EvalInfoResponseHandler,
        )

        template_id = template_details["id"]
        required_keys = template_details["config"]["required_keys"]

        mapping = {}

        for key in required_keys:
            if key not in required_keys_to_column_names:
                raise DatasetValidationError(
                    f"Required key '{key}' not found in required_keys_to_column_names for template '{eval_template}'"
                )
            column_name = required_keys_to_column_names[key]
            if not column_name:
                raise DatasetValidationError(f"Column name mapping for key '{key}' cannot be empty.")
            column_id = self.get_column_id(column_name)
            if not column_id:
                raise DatasetError(f"Column '{column_name}' (mapped from key '{key}') not found in dataset '{self.dataset_config.name}'.")
            mapping[key] = column_id

        eval_config = {
            "template_id": template_id,
            "run": run,
            "name": name,
            "saveAsTemplate": save_as_template,
            "config": {
                "mapping": mapping,
                "config": config or {},
                "reasonColumn": reason_column,
            },
        }

        # Add optional fields to the top level payload
        if model:
            eval_config["model"] = model
        if error_localizer:
            eval_config["error_localizer"] = error_localizer
        if kb_id:
            eval_config["kb_id"] = kb_id

        url = f"{self._base_url}/model-hub/develops/{str(self.dataset_config.id)}/add_user_eval/"
        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=eval_config, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

        return self

    def get_eval_stats(self) -> Dict[str, Any]:
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to get evaluation stats.")
        url = (
            self._base_url
            + "/"
            + Routes.dataset_eval_stats.value.format(
                dataset_id=str(self.dataset_config.id)
            )
        )
        return self.request_with_retry(
            config=RequestConfig(method=HttpMethod.GET, url=url, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def add_optimization(
        self,
        optimization_name: str,
        prompt_column_name: str,
        optimize_type: str = "PROMPT_TEMPLATE",
        model_config: Optional[Dict[str, Any]] = None,
    ) -> "Dataset":

        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset must be configured with an ID to add an optimization.")
        if not optimization_name:
            raise DatasetValidationError("Optimization name cannot be empty.")
        if not prompt_column_name:
            raise DatasetValidationError("Prompt column name for optimization cannot be empty.")

        valid_optimize_types = ["PROMPT_TEMPLATE", "MODEL_PARAMETERS", "HYBRID"]
        if optimize_type not in valid_optimize_types:
            raise DatasetValidationError(
                f"Invalid optimize_type: '{optimize_type}'. Must be one of: {', '.join(valid_optimize_types)}"
            )

        column_id = self.get_column_id(prompt_column_name)
        if not column_id:
            raise DatasetError(
                f"Prompt Column '{prompt_column_name}' not found in dataset '{self.dataset_config.name}'"
            )

        # Try to get metrics that use this column
        metrics_url = f"{self._base_url}/model-hub/metrics/by-column/"
        try:
            metrics_response = self.request_with_retry(
                config=RequestConfig(
                    method=HttpMethod.GET, url=metrics_url, params={"column_id": column_id}, timeout=DEFAULT_API_TIMEOUT
                ),
                response_handler=DatasetResponseHandler,
            )

            # The backend already filters metrics that use the specified column
            # so we can directly extract the IDs
            eval_template_ids = [metric["id"] for metric in metrics_response["result"]]

        except Exception as e:
            # If we can't get metrics by column, try to get all evaluations for this dataset
            print(f"Warning: Could not get metrics by column ({e}). Trying alternative approach...")
            eval_template_ids = []

        # If no metrics found by column, try to get all evaluations for this dataset
        if not eval_template_ids:
            try:
                # Get all evaluations for this dataset
                eval_stats = self.get_eval_stats()
                if isinstance(eval_stats, dict) and "result" in eval_stats:
                    eval_template_ids = [metric["id"] for metric in eval_stats["result"] if isinstance(metric, dict) and metric.get("id")]
                elif isinstance(eval_stats, list):
                    eval_template_ids = [metric["id"] for metric in eval_stats if isinstance(metric, dict) and metric.get("id")]
                
                print(f"Found {len(eval_template_ids)} evaluation templates in dataset")
                
            except Exception as e:
                print(f"Warning: Could not get evaluation stats ({e})")

        if not eval_template_ids:
            raise DatasetError(
                f"No evaluation templates found for optimization in dataset '{self.dataset_config.name}'. "
                f"Please ensure you have added evaluations to the dataset before setting up optimization. "
                f"The column '{prompt_column_name}' needs to be referenced by at least one evaluation."
            )

        # Create user_eval_template_mapping (mapping eval template IDs to themselves)
        user_eval_template_mapping = {str(eval_id): str(eval_id) for eval_id in eval_template_ids}
        
        payload = {
            "name": optimization_name,
            "column_id": column_id,
            "optimize_type": optimize_type,
            "user_eval_template_ids": eval_template_ids,
            "dataset_id": str(self.dataset_config.id),
            "model_config": model_config or {},
            "messages": [],  # Required field, empty array for now
            "user_eval_template_mapping": user_eval_template_mapping,
        }

        opt_url = f"{self._base_url}/model-hub/optimisation/create/"
        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=opt_url, json=payload, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

        return self

    # Protected internal methods
    def _fetch_dataset_config(self, dataset_name: str) -> DatasetConfig:
        if not dataset_name:
            raise DatasetValidationError("Dataset name cannot be empty when fetching configuration.")
        url = f"{self._base_url}/{Routes.dataset_names.value}"
        try:
            dataset_config_obj = self.request_with_retry(
                config=RequestConfig(
                    method=HttpMethod.GET,
                    url=url,
                    params={"search_text": dataset_name},
                    timeout=DEFAULT_API_TIMEOUT,
                ),
                response_handler=DatasetResponseHandler,
            )
            if not isinstance(dataset_config_obj, DatasetConfig):
                 raise DatasetError(f"Fetched configuration for '{dataset_name}' is not a valid DatasetConfig object.")
            return dataset_config_obj
        except DatasetNotFoundError as e:
            raise e
        except DatasetError:
            raise
        except Exception as e: # Catch other unexpected errors during the request
            raise DatasetError(f"An unexpected error occurred while fetching dataset config for '{dataset_name}': {e}")

    def _create_dataset(
        self,
        config: DatasetConfig,
        source: Optional[Union[str, HuggingfaceDatasetConfig]],
    ) -> DatasetConfig:
        """Internal method for dataset creation logic"""
        if source is None:
            return self._create_empty_dataset(config)
        elif isinstance(source, str):
            if not os.path.exists(source):
                raise DatasetValidationError(f"File not found at source path: {source}")
            return self._create_from_file(config, source)
        elif isinstance(source, HuggingfaceDatasetConfig):
            return self._create_from_huggingface(config, source)
        else:
            raise DatasetValidationError(f"Unsupported source type for dataset creation: {type(source)}")

    def _create_empty_dataset(self, config: DatasetConfig) -> DatasetConfig:
        """Create an empty dataset"""
        payload = {
            "new_dataset_name": config.name,
            "model_type": config.model_type.value,
        }
        url = f"{self._base_url}/{Routes.dataset_empty.value}"
        return self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def _create_from_file(self, config: DatasetConfig, file_path: str) -> DatasetConfig:
        """Create dataset from local file"""
        supported_extensions = [".csv", ".xlsx", ".xls", ".json", ".jsonl"]
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in supported_extensions:
            raise DatasetValidationError(
                f"Unsupported file format: {file_ext}. Must be one of: {', '.join(supported_extensions)}"
            )

        try:
            # Use context manager to properly close the file
            with open(file_path, "rb") as f:
                file_content = f.read()
            files = {"file": (os.path.basename(file_path), file_content)}
        except IOError as e:
            raise DatasetError(f"Error reading file {file_path}: {e}")
            
        data = {"model_type": config.model_type.value, "new_dataset_name": config.name}
        url = f"{self._base_url}/{Routes.dataset_local.value}"

        return self.request_with_retry(
            config=RequestConfig(
                method=HttpMethod.POST, url=url, data=data, files=files, timeout=DEFAULT_API_TIMEOUT
            ),
            response_handler=DatasetResponseHandler,
        )

    def _create_from_huggingface(
        self, config: DatasetConfig, hf_config: HuggingfaceDatasetConfig
    ) -> DatasetConfig:
        """Create dataset from Hugging Face"""
        data = {
            "new_dataset_name": config.name,
            "huggingface_dataset_name": hf_config.name,
            "model_type": config.model_type.value,
        }
        if hf_config.split:
            data["huggingface_dataset_split"] = hf_config.split
        if hf_config.subset:
            data["huggingface_dataset_config"] = hf_config.subset
        if hf_config.num_rows:
            data["num_rows"] = hf_config.num_rows

        url = f"{self._base_url}/{Routes.dataset_huggingface.value}"
        return self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, data=data, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def _download_dataset(
        self, name: str, file_path: Optional[str] = None, load_to_pandas: bool = False
    ) -> Union[str, pd.DataFrame]:
        """Internal method for dataset download"""
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset ID must be available in configuration to download.")

        if not file_path:
            file_path = f"{name}.csv"
            logging.info(f"No file path specified. Defaulting to '{file_path}'.")

        url = f"{self._base_url}/{Routes.dataset_table.value.format(dataset_id=str(self.dataset_config.id))}"
        params = {"page_size": PAGE_SIZE, "current_page_index": 0}

        with tqdm(desc="Downloading dataset") as pbar:
            while True:
                pbar.set_postfix({"page": params["current_page_index"] + 1})
                dataset_table = self.request_with_retry(
                    config=RequestConfig(method=HttpMethod.GET, url=url, params=params, timeout=DEFAULT_API_TIMEOUT),
                    response_handler=DatasetResponseHandler,
                )
                dataset_table.to_file(file_path)
                params["current_page_index"] += 1
                if (
                    dataset_table.metadata.get("totalPages")
                    == params["current_page_index"]
                ):
                    pbar.update(1)
                    break

        if load_to_pandas:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                 return pd.DataFrame() 

            if file_path.endswith(".csv"):
                try:
                    return pd.read_csv(file_path)
                except pd.errors.EmptyDataError:
                    return pd.DataFrame()
                except Exception as e:
                    raise DatasetError(f"Error reading CSV file '{file_path}' with pandas: {e}")
            elif file_path.endswith(".json"):
                try:
                    return pd.read_json(file_path, lines=True)
                except pd.errors.EmptyDataError:
                    return pd.DataFrame()
                except ValueError as e: 
                    raise DatasetError(f"Error reading JSON file '{file_path}' with pandas: {e}")
                except Exception as e:
                    raise DatasetError(f"Error reading JSON file '{file_path}' with pandas: {e}")
            else:
                raise DatasetValidationError(f"Unsupported file format for pandas loading: {file_path}")
        return file_path

    def _delete(self) -> None:
        """Internal method to delete dataset"""
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("Dataset ID must be configured for deletion internal call.")

        url = f"{self._base_url}/{Routes.dataset_delete.value}"
        payload = {"dataset_ids": [str(self.dataset_config.id)]}

        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.DELETE, url=url, json=payload, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def _add_columns(self, columns: List[Column]) -> None:
        """Add columns to the dataset"""

        if not self.dataset_config or not getattr(self.dataset_config, "id", None):
            raise DatasetError("No dataset configured with an ID for column addition.")

        if not isinstance(columns, list):
            raise DatasetValidationError("Columns must be a list.")

        if not all(isinstance(column, Column) for column in columns):
            raise DatasetValidationError("Each item in columns list must be a Column object for _add_columns.")

        serialized_columns = [column.to_dict() for column in columns]
        url = f"{self._base_url}/{Routes.dataset_add_columns.value.format(dataset_id=str(self.dataset_config.id))}"
        payload = {
            "new_columns_data": serialized_columns,
        }

        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def _add_rows(self, rows: List[Row], **kwargs) -> None:
        """Add rows to the dataset"""
        if not self.dataset_config or not self.dataset_config.id:
            raise DatasetError("No dataset configured with an ID for row addition")
        
        if not isinstance(rows, list):
            raise DatasetValidationError("Rows must be a list.")
        if not all(isinstance(row, Row) for row in rows):
            raise DatasetValidationError("Each item in rows list must be a Row object for _add_rows.")

        serialized_rows = [row.to_dict() for row in rows]

        url = f"{self._base_url}/{Routes.dataset_add_rows.value.format(dataset_id=str(self.dataset_config.id))}"
        payload = {"rows": serialized_rows}

        self.request_with_retry(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload, timeout=DEFAULT_API_TIMEOUT),
            response_handler=DatasetResponseHandler,
        )

    def request_with_retry(
        self, 
        config: RequestConfig, 
        response_handler: type[ResponseHandler], 
        max_retries: int = 3
    ) -> Any:
        retries = 0
        last_exception: Optional[Exception] = None

        while retries < max_retries:
            try:
                return self.request(config=config, response_handler=response_handler)
            except (ConnectionError, Timeout, ServerError, ServiceUnavailableError) as e:
                last_exception = e
                retries += 1
                if retries >= max_retries:
                    break
                wait_time = 2 ** retries
                logging.warning(f"Request failed with {type(e).__name__}. Retrying request to {config.url} after {wait_time}s (attempt {retries}/{max_retries}). Error: {e}")
                time.sleep(wait_time)
   
        if last_exception is not None:
            raise last_exception # type: ignore
        else:
            raise DatasetError(f"Request failed after {max_retries} retries, but no specific exception was captured.")

    # Class methods for simple operations
    @classmethod
    def _get_instance(
        cls, dataset_config: Optional[DatasetConfig] = None, **kwargs
    ) -> "Dataset":
        """Create a new Dataset instance"""
        return (
            cls(dataset_config=dataset_config, **kwargs)
            if isinstance(cls, type)
            else cls
        )

    @classmethod
    def create_dataset(
        cls,
        dataset_config: DatasetConfig,
        source: Optional[Union[str, HuggingfaceDatasetConfig]] = None,
        **kwargs,
    ) -> "Dataset":
        """Class method for simple dataset creation"""
        if not isinstance(dataset_config, DatasetConfig):
            raise DatasetValidationError("dataset_config must be a DatasetConfig object.")

        instance = cls._get_instance(dataset_config=dataset_config, **kwargs)
        return instance.create(source)

    @classmethod
    def download_dataset(
        cls,
        dataset_name: str,
        file_path: Optional[str] = None,
        load_to_pandas: bool = False,
        **kwargs,
    ) -> Union[str, pd.DataFrame]:
        """Class method for simple dataset download"""
        if not dataset_name:
            raise DatasetValidationError("Dataset name must be provided for download.")
        instance = cls.get_dataset_config(dataset_name, **kwargs)
        return instance.download(file_path, load_to_pandas)

    @classmethod
    def delete_dataset(cls, dataset_name: str, **kwargs) -> None:
        """Class method for simple dataset deletion"""
        if not dataset_name:
            raise DatasetValidationError("Dataset name must be provided for deletion.")
        instance = cls.get_dataset_config(dataset_name, **kwargs)
        instance.delete()

    @classmethod
    def get_dataset_config(
        cls,
        dataset_name: str,
        excluded_datasets: Optional[List[str]] = None,
        **kwargs,
    ) -> "Dataset":
        """Get dataset configuration with caching"""
        cache_key = f"{dataset_name}_{str(excluded_datasets)}"
        
        cached_instance = cls._dataset_instance_cache.get(cache_key)
        if cached_instance:
            return cached_instance

        request_instance = cls._get_instance(**kwargs)
        
        params = {"search_text": dataset_name}
        if excluded_datasets:
            params["excluded_datasets"] = excluded_datasets

        url = f"{request_instance._base_url}/{Routes.dataset_names.value}"
        
        try:
            fetched_dataset_config = request_instance.request_with_retry(
                config=RequestConfig(
                    method=HttpMethod.GET, 
                    url=url, 
                    params=params, 
                    timeout=DEFAULT_API_TIMEOUT
                ),
                response_handler=DatasetResponseHandler,
            )
        except DatasetNotFoundError:
            raise DatasetNotFoundError(f"Dataset named '{dataset_name}' not found (excluded: {excluded_datasets}).")
        except Exception as e:
            raise DatasetError(f"Error fetching configuration for dataset '{dataset_name}': {e}")

        if not isinstance(fetched_dataset_config, DatasetConfig):
            raise DatasetError(f"API did not return a valid DatasetConfig for '{dataset_name}'. Got: {type(fetched_dataset_config)}")

        instance_to_cache = cls(dataset_config=fetched_dataset_config, **kwargs)

        cls._dataset_instance_cache.put(cache_key, instance_to_cache)
        return instance_to_cache

    @classmethod
    def add_dataset_columns(
        cls, dataset_name: str, columns: List[Union[Column, dict]], **kwargs
    ):
        if not dataset_name:
            raise DatasetValidationError("Dataset name must be provided to add columns.")
        if not columns:
            raise DatasetValidationError("Columns list cannot be empty.")
        
        instance = cls.get_dataset_config(dataset_name, **kwargs)
        return instance.add_columns(columns=columns)

    @classmethod
    def add_dataset_rows(
        cls,
        dataset_name: str,
        rows: List[Union[Row, dict]],
        **kwargs,
    ):
        if not dataset_name:
            raise DatasetValidationError("Dataset name must be provided to add rows.")
        if not rows:
            raise DatasetValidationError("Rows list cannot be empty.")

        instance = cls.get_dataset_config(dataset_name, **kwargs)
        return instance.add_rows(rows=rows)
