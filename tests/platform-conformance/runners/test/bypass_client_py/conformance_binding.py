"""A stub Python SDK that IGNORES the guarded transport it is given (test only): the worker's process
guard must still refuse each of its own clients, and every refusal must reach the guard receipt."""

import socket
import urllib.request

import httpx

PACKAGE = {"name": "bypass-client-py", "version": "0.0.0-stub"}


class BypassReport(Exception):
    def __init__(self, classes):
        super().__init__(",".join(f"{k}={v}" for k, v in classes.items()))
        self.classes = classes


def create_client(
    baseUrl, credential, fetch=None, options=None, transport=None, async_transport=None
):
    return {"baseUrl": baseUrl}  # the guarded transport is dropped on purpose


def call(client, sdk, args, **_):
    attempts = {
        "httpx": lambda: httpx.Client(timeout=2, trust_env=False).get(
            "http://bypass-probe.invalid:9/"
        ),
        "urllib": lambda: urllib.request.urlopen(
            "http://bypass-probe2.invalid:9/", timeout=2
        ),
        "socket": lambda: socket.create_connection(
            ("api.futureagi.com", 443), timeout=2
        ),
    }
    classes = {}
    for name, attempt in attempts.items():
        try:
            attempt()
            classes[name] = "reached"
        except Exception as exc:  # swallowed, as a careless SDK would: the receipt must still show it
            classes[name] = type(exc).__name__
    raise BypassReport(classes)


def describe_error(error):
    if isinstance(error, BypassReport):
        return {"errorClass": "BypassReport", "code": str(error)}
    return {"errorClass": type(error).__name__}
