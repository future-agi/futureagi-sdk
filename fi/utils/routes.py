from enum import Enum


class Routes(str, Enum):
    healthcheck = "healthcheck"

    evaluate = "sdk/api/v1/eval/"
    log_model = "sdk/api/v1/log/model/"
    evaluate_template = "sdk/api/v1/eval/{eval_id}/"
    api_keys = "model-hub/api-keys"
    dataset = "model-hub/develops"
    dataset_names = "model-hub/develops/get-datasets-names/"
    dataset_empty = "model-hub/develops/create-empty-dataset/"
    dataset_local = "model-hub/develops/create-dataset-from-local-file/"
    dataset_huggingface = "model-hub/develops/create-dataset-from-huggingface/"
    dataset_table = "model-hub/develops/{dataset_id}/get-dataset-table/"
    dataset_delete = "model-hub/develops/delete_dataset/"
