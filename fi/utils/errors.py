from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Optional, Union

from .constants import (
    API_KEY_ENVVAR_NAME,
    MAX_NUMBER_OF_EMBEDDINGS,
    SECRET_KEY_ENVVAR_NAME,
)
from .types import Environments, ModelTypes


class CustomException(Exception, ABC):
    def __str__(self) -> str:
        return self.error_message()

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def error_message(self) -> str:
        pass


class MissingAuthError(CustomException):
    def __init__(self, fi_api_key: Optional[str], fi_secret_key: Optional[str]) -> None:
        self.missing_api_key = fi_api_key is None
        self.missing_secret_key = fi_secret_key is None

    def __repr__(self) -> str:
        return "Missing_FI_Client_Authentication"

    def error_message(self) -> str:
        missing_list = ["fi_api_key"] if self.missing_api_key else []
        if self.missing_secret_key:
            missing_list.append("fi_secret_key")

        return (
            "FI Client could not obtain credentials. You can pass your fi_api_key and fi_secret_key "
            "directly to the FI Client, or you can set environment variables which will be read if the "
            "keys are not directly passed. "
            "To set the environment variables use the following variable names: \n"
            f" - {API_KEY_ENVVAR_NAME} for the api key\n"
            f" - {SECRET_KEY_ENVVAR_NAME} for the secret key\n"
            f"Missing: {missing_list}"
        )


class InvalidAuthError(CustomException):
    """Exception raised when API authentication fails due to invalid credentials"""

    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return "Invalid_FI_Client_Authentication"

    def __str__(self) -> str:
        return self.error_message()

    def error_message(self) -> str:
        return (
            "Invalid FI Client Authentication, please check your api key and secret key"
        )


class InvalidAdditionalHeaders(CustomException):
    """Exception raised when additional headers are invalid"""

    def __repr__(self) -> str:
        return "Invalid_Additional_Headers"

    def __init__(self, invalid_headers: Iterable) -> None:
        self.invalid_header_names = invalid_headers

    def error_message(self) -> str:
        return (
            "Found invalid additional header, cannot use reserved headers named: "
            f"{', '.join(map(str, self.invalid_header_names))}."
        )


class InvalidNumberOfEmbeddings(CustomException):
    """Exception raised when the number of embeddings is invalid"""

    def __init__(self, number_of_embeddings: int) -> None:
        self.number_of_embeddings = number_of_embeddings

    def __repr__(self) -> str:
        return "Invalid_Number_Of_Embeddings"

    def error_message(self) -> str:
        return (
            f"The schema contains {self.number_of_embeddings} different embeddings when a maximum of "
            f"{MAX_NUMBER_OF_EMBEDDINGS} is allowed."
        )


class InvalidValueType(CustomException):
    """Exception raised when the value type is invalid"""

    def __init__(
        self,
        value_name: str,
        value: Union[bool, int, float, str],
        correct_type: str,
    ) -> None:
        self.value_name = value_name
        self.value = value
        self.correct_type = correct_type

    def __repr__(self) -> str:
        return "Invalid_Value_Type"

    def error_message(self) -> str:
        return (
            f"{self.value_name} with value {self.value} is of type {type(self.value).__name__}, "
            f"but expected From {self.correct_type}"
        )


class InvalidSupportedType(CustomException):
    """Exception raised when the supported type is invalid"""

    def __init__(
        self,
        value_name: str,
        value: Union[ModelTypes, Environments],
        correct_type: str,
    ) -> None:
        self.value_name = value_name
        self.value = value
        self.correct_type = correct_type

    def __repr__(self) -> str:
        return "Invalid_Value_Type"

    def error_message(self) -> str:
        return (
            f"{self.value_name} with value {self.value} is noy supported as of now, "
            f"supported model types are {self.correct_type}"
        )


class MissingRequiredKey(CustomException):
    def __init__(self, field_name, missing_key):
        self.field_name = field_name
        self.missing_key = missing_key

    def __repr__(self) -> str:
        return "Missing_Required_Key"

    def error_message(self) -> str:
        return f"Missing required key '{self.missing_key}' in {self.field_name}."


class MissingRequiredConfigForEvalTemplate(CustomException):
    def __init__(self, missing_key, eval_template_name):
        self.missing_key = missing_key
        self.eval_template_name = eval_template_name

    def __repr__(self) -> str:
        return "Missing_Required_Config_For_Eval_Template"

    def error_message(self) -> str:
        return f"Missing required config '{self.missing_key}' for eval template {self.eval_template_name}."
