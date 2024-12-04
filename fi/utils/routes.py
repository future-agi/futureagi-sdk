from enum import Enum


class Routes(str, Enum):
    healthcheck = "healthcheck"

    evaluate = "sdk/api/v1/eval/"
    log_model = "sdk/api/v1/log/model/"
    api_keys = "model_hub/api-keys"
    dataset = "model-hub/dataset"
    dataset_empty = "model-hub/dataset/empty"
    dataset_local = "model-hub/dataset/local"
    dataset_huggingface = "model-hub/dataset/huggingface"
    dataset_table = "model-hub/dataset/{dataset_id}/table"
    dataset_delete = "model-hub/dataset/{dataset_id}"
    dataset_clone = "model-hub/dataset/{dataset_id}/clone"
