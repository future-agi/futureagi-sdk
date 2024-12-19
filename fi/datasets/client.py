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

    This client can be used in two ways:
    1. As class methods for simple one-off operations:
        DatasetClient.download_dataset("my_dataset")

    2. As an instance for chained operations:
        client = DatasetClient(dataset_config=config)
        client.create().download("output.csv").delete()
    """

    _dataset_id_cache = {}

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        dataset_config: Optional[DatasetConfig] = None,
        **kwargs,
    ):
        super().__init__(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
            **kwargs,
        )
        self.dataset_config = dataset_config

    # Instance methods for chaining
    def create(
        self, source: Optional[Union[str, HuggingfaceDatasetConfig]] = None
    ) -> "DatasetClient":
        """Create a dataset and return self for chaining"""
        if not self.dataset_config:
            raise ValueError("dataset_config must be set")

        response = self._create_dataset(self.dataset_config, source)
        self.dataset_config.id = response.id
        return self

    def download(
        self, file_path: Optional[str] = None, load_to_pandas: bool = False
    ) -> Union["DatasetClient", pd.DataFrame]:
        """Download dataset and return self or DataFrame"""
        result = self._download_dataset(
            self.dataset_config.name, file_path, load_to_pandas
        )
        return result if load_to_pandas else self

    def delete(self) -> None:
        """Delete the current dataset"""
        self._delete()
        self.dataset_config = None

    def get_config(self) -> DatasetConfig:
        """Get the current dataset configuration"""
        if not self.dataset_config:
            raise ValueError("No dataset configured")
        return self.dataset_config

    # Protected internal methods
    def _create_dataset(
        self,
        config: DatasetConfig,
        source: Optional[Union[str, HuggingfaceDatasetConfig]],
    ) -> DatasetConfig:
        """Internal method for dataset creation logic"""
        if source is None:
            return self._create_empty_dataset(config)
        elif isinstance(source, str):
            return self._create_from_file(config, source)
        elif isinstance(source, HuggingfaceDatasetConfig):
            return self._create_from_huggingface(config, source)
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    def _create_empty_dataset(self, config: DatasetConfig) -> DatasetConfig:
        """Create an empty dataset"""
        payload = {
            "new_dataset_name": config.name,
            "model_type": config.model_type.value,
        }
        url = f"{self._base_url}/{Routes.dataset_empty.value}"
        return self.request(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload),
            response_handler=DatasetResponseHandler,
        )

    def _create_from_file(self, config: DatasetConfig, file_path: str) -> DatasetConfig:
        """Create dataset from local file"""
        supported_extensions = [".csv", ".xlsx", ".xls", ".json", ".jsonl"]
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in supported_extensions:
            raise ValueError(
                f"Unsupported file format. Must be one of: {', '.join(supported_extensions)}"
            )

        files = {"file": (os.path.basename(file_path), open(file_path, "rb").read())}
        data = {"model_type": config.model_type.value, "new_dataset_name": config.name}
        url = f"{self._base_url}/{Routes.dataset_local.value}"

        return self.request(
            config=RequestConfig(
                method=HttpMethod.POST, url=url, data=data, files=files
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
        if hf_config.num_rows:
            data["num_rows"] = hf_config.num_rows

        url = f"{self._base_url}/{Routes.dataset_huggingface.value}"
        return self.request(
            config=RequestConfig(method=HttpMethod.POST, url=url, data=data),
            response_handler=DatasetResponseHandler,
        )

    def _download_dataset(
        self, name: str, file_path: Optional[str] = None, load_to_pandas: bool = False
    ) -> Union[str, pd.DataFrame]:
        """Internal method for dataset download"""
        if not file_path:
            file_path = get_tempfile_path(
                DATASET_TEMP_FILE_PREFIX, DATASET_TEMP_FILE_SUFFIX
            )

        url = f"{self._base_url}/{Routes.dataset_table.value.format(dataset_id=str(self.dataset_config.id))}"
        data = {"page_size": PAGE_SIZE, "current_page_index": 0}

        with tqdm(desc="Downloading dataset") as pbar:
            while True:
                pbar.set_postfix({"page": data["current_page_index"] + 1})
                dataset_table = self.request(
                    config=RequestConfig(method=HttpMethod.POST, url=url, json=data),
                    response_handler=DatasetResponseHandler,
                )
                dataset_table.to_file(file_path)
                data["current_page_index"] += 1
                if (
                    dataset_table.metadata.get("totalPages")
                    == data["current_page_index"]
                ):
                    pbar.update(1)
                    break

        if load_to_pandas:
            if file_path.endswith(".csv"):
                return pd.read_csv(file_path)
            elif file_path.endswith(".json"):
                return pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported format for pandas: {file_path}")
        return file_path

    def _delete(self) -> None:
        """Internal method to delete dataset"""
        if not self.dataset_config or not self.dataset_config.id:
            raise ValueError("No dataset configured for deletion")

        url = f"{self._base_url}/{Routes.dataset_delete.value}"
        payload = {"dataset_ids": [str(self.dataset_config.id)]}

        self.request(
            config=RequestConfig(method=HttpMethod.DELETE, url=url, json=payload),
            response_handler=DatasetResponseHandler,
        )

    # Class methods for simple operations
    @classmethod
    def _get_instance(cls, **kwargs) -> "DatasetClient":
        """Create a new DatasetClient instance"""
        return cls(**kwargs) if isinstance(cls, type) else cls

    @classmethod
    def create_dataset(
        cls,
        dataset_config: DatasetConfig,
        source: Optional[Union[str, HuggingfaceDatasetConfig]] = None,
        **kwargs,
    ) -> "DatasetClient":
        """Class method for simple dataset creation"""
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
        instance = cls.get_dataset_config(dataset_name, **kwargs)
        return instance.download(file_path, load_to_pandas)

    @classmethod
    def delete_dataset(cls, dataset_name: str, **kwargs) -> None:
        """Class method for simple dataset deletion"""
        instance = cls.get_dataset_config(dataset_name, **kwargs)
        instance.delete()

    @classmethod
    def get_dataset_config(
        cls,
        dataset_name: str,
        excluded_datasets: Optional[List[str]] = None,
        **kwargs,
    ) -> "DatasetClient":
        """Get dataset configuration with caching"""
        cache_key = f"{dataset_name}_{str(excluded_datasets)}"
        if cache_key in cls._dataset_id_cache:
            return cls._dataset_id_cache[cache_key]

        instance = cls._get_instance(**kwargs)
        payload = {"search_text": dataset_name}
        if excluded_datasets:
            payload["excluded_datasets"] = excluded_datasets

        url = f"{instance._base_url}/{Routes.dataset_names.value}"
        dataset_config = instance.request(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=payload),
            response_handler=DatasetResponseHandler,
        )

        instance.dataset_config = dataset_config
        cls._dataset_id_cache[cache_key] = instance
        return instance
