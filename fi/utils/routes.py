from enum import Enum


class Routes(str, Enum):
    healthcheck = "healthcheck"

    evaluate = "sdk/api/v1/eval/"
    log = "sdk/api/v1/log/model/"
    api_keys = "model_hub/api-keys"
