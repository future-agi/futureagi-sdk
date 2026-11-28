"""Delivery controls for canonical loopback URLs and an opted-in named host."""

from __future__ import annotations

import socket
from contextlib import closing, suppress

import pytest
from pydantic import ValidationError

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.gateway import Gateway
from fi.platform import Client
from tests.test_plain_http_key_guards import KEY, SECRET, net  # noqa: F401


@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "ordinary.example.test"])
def test_supported_host_delivers_key_directly_with_opt_in(monkeypatch, net, sender, host):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    original = socket.getaddrinfo
    mapped = []

    def resolve(name, *args, **kwargs):
        text = name.decode("ascii") if isinstance(name, bytes) else name
        if text in {"localhost", "ordinary.example.test"}:
            mapped.append(text)
            name = "127.0.0.1"
        return original(name, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    base_url = f"http://{host}:{net.target.port}"
    if sender == "http-client":
        with closing(HttpClient(base_url=base_url, default_headers={"X-Api-Key": KEY, "X-Secret-Key": SECRET})) as client:
            client.request(RequestConfig(method=HttpMethod.GET, url=f"{base_url}/v1/ping", retry_attempts=1, timeout=3))
    elif sender == "platform-sync":
        with Client(base_url=base_url, api_key=KEY, secret_key=SECRET, max_retries=0, timeout=3) as client:
            client.request("GET", "/v1/ping", unwrap=None)
    else:
        with Gateway(base_url=base_url, api_key=KEY, max_retries=0, timeout=3) as client:
            # The listener replies with {}, not a model list.
            with suppress(ValidationError):
                client.models.list()

    assert net.target.connections >= 1 and net.target.marker_bytes() > 0, net.report()
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), net.report()
    if host == "ordinary.example.test":
        assert host in mapped
