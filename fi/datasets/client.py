import os
from typing import List, Optional, Union

import pandas as pd
from requests import Response
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
from fi.utils.constants import (
    DATASET_TEMP_FILE_PREFIX,
    DATASET_TEMP_FILE_SUFFIX,
    PAGE_SIZE,
)
from fi.utils.errors import InvalidAuthError
from fi.utils.routes import Routes
from fi.utils.utils import get_tempfile_path


class DatasetResponseHandler(ResponseHandler[DatasetConfig, DatasetTable]):

    """Handles responses for dataset requests"""

    @classmethod
    def _parse_success(cls, response: Response) -> Union[DatasetConfig, DatasetTable]:
        """Parse successful response into DatasetResponse"""
        data = response.json()
        if response.url.endswith(Routes.dataset_names.value):
            datasets = data["result"]["datasets"]
            if not datasets:
                raise ValueError("No dataset found")
            if len(datasets) > 1:
                raise ValueError(
                    "Multiple datasets found. Please specify a dataset name."
                )
            return DatasetConfig(
                id=datasets[0]["datasetId"],
                name=datasets[0]["name"],
                model_type=datasets[0]["modelType"],
            )
        elif Routes.dataset_table.value.split("/")[-2] in response.url:
            id = response.url.split("/")[-3]
            columns = [
                Column(
                    id=column["id"],
                    name=column["name"],
                    data_type=column["dataType"],
                    source=column["originType"],
                    source_id=column["sourceId"],
                    is_frozen=column["isFrozen"]["isFrozen"]
                    if column["isFrozen"] is not None
                    else False,
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
                            value_infos=[value.get("valueInfos")]
                            if value.get("valueInfos")
                            else None,
                            metadata=value.get("metadata"),
                            status=value.get("status"),
                            failure_reason=value.get("failureReason"),
                        )
                    )
                rows.append(Row(id=row_id, order=order, cells=cells))
            metadata = data["result"]["metadata"]
            return DatasetTable(id=id, columns=columns, rows=rows, metadata=metadata)
        elif response.url.endswith(Routes.dataset_empty.value):
            return DatasetConfig(
                id=data["result"]["datasetId"],
                name=data["result"]["datasetName"],
                model_type=data["result"]["datasetModelType"],
            )
        elif response.url.endswith(Routes.dataset_local.value):
            return DatasetConfig(
                id=data["result"]["datasetId"],
                name=data["result"]["datasetName"],
                model_type=data["result"]["datasetModelType"],
            )
        elif response.url.endswith(Routes.dataset_huggingface.value):
            return DatasetConfig(
                id=data["result"]["datasetId"],
                name=data["result"]["datasetName"],
                model_type=data["result"]["datasetModelType"],
            )
        else:
            return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code == 400:
            response.raise_for_status()
        if response.status_code == 403:
            raise InvalidAuthError()


class DatasetClient(APIKeyAuth):
    """Manager class for handling datasets

    A client for managing datasets including creation, deletion, downloading and metadata operations.
    Provides functionality to work with empty datasets, local files, and Hugging Face datasets.

    Attributes:
        _dataset_id_cache (dict): Class-level cache for storing dataset IDs
        dataset_config (DatasetConfig): Configuration for the current dataset
    """

    _dataset_id_cache = {}

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the dataset manager

        Args:
            fi_api_key (str, optional): API key for authentication
            fi_secret_key (str, optional): Secret key for authentication
            fi_base_url (str, optional): Base URL of the API

        Kwargs:
            dataset_config (DatasetConfig): Dataset configuration

        Returns:
            DatasetClient: Instance of DatasetClient
        """
        super().__init__(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
            **kwargs,
        )
        self.dataset_config = None
        if kwargs.get("dataset_config"):
            self.dataset_config = kwargs.get("dataset_config")

    @classmethod
    def _get_instance(
        cls,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ) -> "DatasetClient":
        """Create and return an instance of DatasetClient

        Factory method to create a new DatasetClient instance or return existing one.

        Args:
            fi_api_key (str, optional): API key for authentication
            fi_secret_key (str, optional): Secret key for authentication
            fi_base_url (str, optional): Base URL of the API

        Kwargs:
            dataset_config (DatasetConfig): Dataset configuration

        Returns:
            DatasetClient: New or existing instance of DatasetClient
        """

        if isinstance(cls, type):
            # Called on class
            return cls(
                fi_api_key=fi_api_key,
                fi_secret_key=fi_secret_key,
                fi_base_url=fi_base_url,
                **kwargs,
            )
        else:
            # Called on instance
            return cls

    @classmethod
    def create_dataset(
        cls,
        dataset_config: Optional[DatasetConfig] = None,
        source: Optional[Union[str, HuggingfaceDatasetConfig]] = None,
        **kwargs,
    ) -> "DatasetClient":
        """Create a new dataset

        Creates a new dataset either empty, from a local file, or from Hugging Face.

        Args:
            dataset_config (DatasetConfig): Configuration for the new dataset
            source (Optional[Union[str, HuggingfaceDatasetConfig]]): Source for dataset creation.
                - If None: Creates empty dataset
                - If str: Path to local file (.csv, .xlsx, .json, or .jsonl)
                - If HuggingfaceDatasetConfig: Configuration for importing from Hugging Face

        Returns:
            DatasetClient: Instance of DatasetClient with the created dataset

        Raises:
            ValueError: If file format is not supported or file cannot be processed
            InvalidAuthError: If authentication fails
        """
        instance = cls._get_instance(dataset_config=dataset_config, **kwargs)

        if source is None:
            # Create empty dataset
            payload = {
                "new_dataset_name": instance.dataset_config.name,
                "model_type": instance.dataset_config.model_type.value,
            }
            url = instance._base_url + "/" + Routes.dataset_empty.value
            response = instance.request(
                config=RequestConfig(method=HttpMethod.POST, url=url, json=payload),
                response_handler=DatasetResponseHandler,
            )

        elif isinstance(source, str):
            # Create from local file
            supported_extensions = [".csv", ".xlsx", ".xls", ".json", ".jsonl"]
            file_ext = os.path.splitext(source)[1].lower()
            if file_ext not in supported_extensions:
                raise ValueError(
                    f"Unsupported file format. File must have one of these extensions: {', '.join(supported_extensions)}"
                )

            files = {"file": (os.path.basename(source), open(source, "rb").read())}
            data = {}
            if instance.dataset_config.model_type:
                data["model_type"] = instance.dataset_config.model_type.value
            if instance.dataset_config.name:
                data["new_dataset_name"] = instance.dataset_config.name
            url = instance._base_url + "/" + Routes.dataset_local.value

            response = instance.request(
                config=RequestConfig(
                    method=HttpMethod.POST, url=url, data=data, files=files
                ),
                response_handler=DatasetResponseHandler,
            )

        elif isinstance(source, HuggingfaceDatasetConfig):
            # Create from Hugging Face dataset
            data = {
                "new_dataset_name": instance.dataset_config.name,
                "huggingface_dataset_name": source.name,
            }
            if instance.dataset_config.model_type:
                data["model_type"] = instance.dataset_config.model_type.value
            if source.split:
                data["huggingface_dataset_split"] = source.split
            if source.num_rows:
                data["num_rows"] = source.num_rows
            url = instance._base_url + "/" + Routes.dataset_huggingface.value

            response = instance.request(
                config=RequestConfig(method=HttpMethod.POST, url=url, data=data),
                response_handler=DatasetResponseHandler,
            )

        # Update the dataset config with the new dataset ID
        instance.dataset_config.id = response.id
        return instance

    @classmethod
    def download_dataset(
        cls,
        dataset_name: Optional[str] = None,
        file_path: Optional[str] = None,
        load_to_pandas: Optional[bool] = False,
    ) -> Union[str, pd.DataFrame]:
        """Download dataset to file

        Downloads a dataset to a local file or pandas DataFrame.

        Args:
            dataset_name (str, optional): Name of the dataset
            file_path (str, optional): File path to save the dataset
            load_to_pandas (bool, optional): Whether to return as pandas DataFrame

        Returns:
            Union[str, pd.DataFrame]: File path or pandas DataFrame containing the dataset

        Raises:
            ValueError: If file format is not supported
            InvalidAuthError: If authentication fails
        """
        # Get the dataset metadata
        instance = cls.get_dataset(dataset_name)

        # Prepare request and data
        url = (
            instance._base_url
            + "/"
            + Routes.dataset_table.value.format(
                dataset_id=str(instance.dataset_config.id)
            )
        )
        data = {}
        data["page_size"] = PAGE_SIZE
        data["current_page_index"] = 0

        # Prepare file path
        if file_path is None:
            file_path = get_tempfile_path(
                DATASET_TEMP_FILE_PREFIX, DATASET_TEMP_FILE_SUFFIX
            )

        # Make the request
        with tqdm(desc="Downloading dataset") as pbar:
            while True:
                pbar.set_postfix({"page": data["current_page_index"] + 1})
                dataset_table = instance.request(
                    config=RequestConfig(method=HttpMethod.POST, url=url, json=data),
                    response_handler=DatasetResponseHandler,
                )
                _ = dataset_table.to_file(file_path)
                data["current_page_index"] += 1
                if (
                    dataset_table.metadata.get("totalPages")
                    == data["current_page_index"]
                ):
                    pbar.update(1)
                    break

        # Load the dataset to pandas if requested
        if load_to_pandas:
            if file_path.endswith(".csv"):
                return pd.read_csv(file_path)
            elif file_path.endswith(".json"):
                return pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        else:
            return instance

    @classmethod
    def get_dataset(
        cls,
        dataset_name: str,
        excluded_datasets: Optional[List[str]] = None,
        **kwargs,
    ) -> DatasetConfig:
        """Get the metadata of a dataset

        Retrieves metadata for a dataset, with caching support.

        Args:
            dataset_name (str): Name of the dataset
            excluded_datasets (List[str], optional): List of dataset IDs to exclude

        Kwargs:
            fi_api_key (str): API key for authentication
            fi_secret_key (str): Secret key for authentication
            fi_base_url (str): Base URL of the API

        Returns:
            DatasetConfig: Metadata of the dataset

        Raises:
            ValueError: If no dataset or multiple datasets found
            InvalidAuthError: If authentication fails
        """
        # Check cache and return instance if found
        cache_key = f"{dataset_name}_{str(excluded_datasets)}"
        if cache_key in cls._dataset_id_cache:
            return cls._dataset_id_cache[cache_key]

        # Get the instance of the dataset client
        instance = cls._get_instance(**kwargs)

        # Prepare request and data
        payload = {"search_text": dataset_name}
        if excluded_datasets:
            payload["excluded_datasets"] = excluded_datasets
        url = instance._base_url + "/" + Routes.dataset_names

        # Make the request
        dataset_config = instance.request(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload),
            response_handler=DatasetResponseHandler,
        )
        instance.dataset_config = dataset_config

        # Store in cache before returning
        cls._dataset_id_cache[cache_key] = instance
        return instance

    @classmethod
    def delete_dataset(
        cls, dataset_name: Optional[str] = None, **kwargs
    ) -> "DatasetClient":
        """Delete a dataset

        Deletes a dataset by name.

        Args:
            dataset_name (str): Name of the dataset to delete

        Kwargs:
            fi_api_key (str): API key for authentication
            fi_secret_key (str): Secret key for authentication
            fi_base_url (str): Base URL of the API

        Returns:
            None

        Raises:
            InvalidAuthError: If authentication fails
        """
        # Get the dataset metadata
        instance = cls.get_dataset(dataset_name, **kwargs)

        # Prepare request and data
        url = instance._base_url + "/" + Routes.dataset_delete.value
        payload = {"dataset_ids": [str(instance.dataset_config.id)]}

        # Make the request
        instance.request(
            config=RequestConfig(method=HttpMethod.DELETE, url=url, json=payload),
            response_handler=DatasetResponseHandler,
        )
        return instance
