"""Released dataset constructors bridge to fi.errors only while SDK-owned.

C3 for each Name in RateLimitError / ServerError:
fi.utils.errors.Name, fi.errors.Name, fi.errors.FutureAGIAPIError,
fi.utils.errors.DatasetError, fi._sdk_exception.SDKException,
Exception, BaseException, object.
"""

import copy
import inspect
import pickle

import pytest
from requests import Response

import fi
from fi import errors as core
from fi._core.errors import api_error
from fi._sdk_exception import SDKException
from fi.datasets.dataset import DatasetResponseHandler
from fi.utils import errors as legacy


NAMES = ("RateLimitError", "ServerError")
STATUSES = (429, 500, 501, 502, 504, 599)
MESSAGES = {
    "RateLimitError": (
        "Rate Limit Exceeded, please contact FutureAGI support at "
        "support@futureagi.com or check your current plan."
    ),
    "ServerError": "Internal Server Error, please contact FutureAGI support at support@futureagi.com.",
}
CODES = {"RateLimitError": "RATE_LIMIT_EXCEEDED", "ServerError": "SERVER_ERROR"}
REPRS = {"RateLimitError": "Rate_Limit_Exceeded", "ServerError": "Server_Error"}


def dataset_failure(status, body=b'{"message":"fixture failure"}'):
    response = Response()
    response.status_code = status
    response._content = body
    response.encoding = "utf-8"
    try:
        DatasetResponseHandler._handle_error(response)
    except Exception as error:
        return error
    pytest.fail("the dataset handler must raise an error")


def name_for(status):
    return "RateLimitError" if status == 429 else "ServerError"


@pytest.mark.parametrize("status", STATUSES)
def test_dataset_status_has_both_hierarchies(status):
    error = dataset_failure(status)
    name = name_for(status)
    assert isinstance(error, getattr(legacy, name))
    assert isinstance(error, legacy.DatasetError)
    assert isinstance(error, SDKException)
    assert isinstance(error, getattr(core, name))
    assert isinstance(error, core.FutureAGIAPIError)


@pytest.mark.parametrize("status", STATUSES)
def test_dataset_status_is_caught_by_canonical_and_legacy_classes(status):
    error = dataset_failure(status)
    for expected in (getattr(core, name_for(status)), legacy.DatasetError, getattr(legacy, name_for(status))):
        caught = None
        try:
            raise error
        except expected as match:
            caught = match
        except Exception:
            pass
        assert caught is error, expected.__name__


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("case", ("default", "empty", "message", "cause", "message-cause"))
def test_released_constructor_signature_messages_and_attributes(name, case):
    cls = getattr(legacy, name)
    cause = ValueError("fixture cause") if "cause" in case else None
    message = "fixture message" if "message" in case else "" if case == "empty" else None
    error = cls() if case == "default" else cls(message, cause)
    assert str(error) == (message or MESSAGES[name])
    assert error.args == (message or MESSAGES[name],)
    assert error.custom_message == message
    assert error.__cause__ is cause
    assert error.get_message() == MESSAGES[name]
    assert error.get_error_code() == CODES[name]
    assert repr(error) == REPRS[name]
    parameters = inspect.signature(cls).parameters
    assert list(parameters) == ["message", "cause"]
    assert all(p.default is None for p in parameters.values())
    assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in parameters.values())
    keyword = cls(message=message, cause=cause)
    assert (keyword.args, keyword.custom_message, keyword.__cause__) == (error.args, message, cause)


@pytest.mark.parametrize("name", NAMES)
def test_dataset_mro_is_the_documented_c3_linearization(name):
    assert getattr(legacy, name).__mro__ == (
        getattr(legacy, name), getattr(core, name), core.FutureAGIAPIError,
        legacy.DatasetError, SDKException, Exception, BaseException, object,
    )


@pytest.mark.parametrize("name", NAMES)
def test_python_root_does_not_add_error_aliases(name):
    assert not hasattr(fi, name)
    assert name not in fi.__all__


@pytest.mark.parametrize("status", (429, 500, 503, 599))
def test_core_errors_keep_canonical_identity_without_dataset_membership(status):
    error = api_error(status, {"detail": "fixture failure"})
    expected = getattr(core, name_for(status))
    assert type(error) is expected
    assert isinstance(error, core.FutureAGIAPIError)
    assert not isinstance(error, legacy.DatasetError)
    assert not isinstance(error, getattr(legacy, name_for(status)))
    caught = None
    try:
        raise error
    except expected as match:
        caught = match
    assert caught is error


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("method", ("copy", "deepcopy", "pickle"))
@pytest.mark.parametrize("message", (None, "", "fixture message"))
def test_copy_and_pickle_keep_legacy_one_message_reconstruction(name, method, message):
    error = getattr(legacy, name)(message)
    if method == "pickle":
        restored = pickle.loads(pickle.dumps(error))
    else:
        restored = getattr(copy, method)(error)
    assert type(restored) is type(error)
    assert restored.args == error.args
    assert restored.custom_message == message
    assert str(restored) == str(error)
    assert restored.get_message() == error.get_message()
    assert restored.get_error_code() == error.get_error_code()
    assert repr(restored) == repr(error)
    assert restored.__dict__ == error.__dict__


@pytest.mark.parametrize("name", NAMES)
def test_pickle_retains_released_nonserialization_of_exception_cause(name):
    error = getattr(legacy, name)("fixture message", ValueError("fixture cause"))
    restored = pickle.loads(pickle.dumps(error))
    assert restored.__cause__ is None  # Same as the released BaseException reduction.
    assert restored.args == error.args
    assert restored.custom_message == error.custom_message


@pytest.mark.parametrize("status", STATUSES)
def test_legacy_metadata_is_initialized_but_only_nominal(status):
    error = dataset_failure(status)
    to_dict = getattr(error, "to_dict", None)
    assert callable(to_dict)  # Missing on the base: AssertionError, never AttributeError.
    nominal = 429 if status == 429 else 500
    assert error.status == error.status_code == nominal
    assert error.payload is None
    assert error.code == f"http_{nominal}"
    assert to_dict() == {
        "name": name_for(status), "error_code": CODES[name_for(status)],
        "message": "fixture failure", "status_code": nominal, "code": f"http_{nominal}",
    }
    assert all(getattr(error, field) is None for field in (
        "retry_after", "request_id", "idempotency_key", "operation", "upstream_request_id", "receipt_id",
    ))


@pytest.mark.parametrize("status", (429, 500, 502))
@pytest.mark.parametrize("body", (b"", b"not json"))
def test_legacy_mapper_empty_and_non_json_messages_are_unchanged(status, body):
    error = dataset_failure(status, body)
    message = body.decode() or f"HTTP error {status} with no descriptive message."
    assert type(error) is getattr(legacy, name_for(status))
    assert str(error) == message
    assert error.custom_message == message
    assert error.args == (message,)


def test_dataset_503_keeps_its_released_service_unavailable_class():
    error = dataset_failure(503)
    assert type(error) is legacy.ServiceUnavailableError
    assert isinstance(error, legacy.DatasetError)
    assert not isinstance(error, legacy.ServerError)
    assert not isinstance(error, core.ServerError)
