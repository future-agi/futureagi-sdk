"""Callback dispatch order and error isolation."""

import pytest
from typing import Any
from fi.gateway._base_client import RequestOptions
from ._base_client_fixtures import _make_sync_client


class TestCallbackDispatch:
    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    def test_callbacks_called_in_order(self) -> None:
        order: list[str] = []

        class CB1:
            def on_request_start(self, *args: Any) -> None:
                order.append("cb1")

        class CB2:
            def on_request_start(self, *args: Any) -> None:
                order.append("cb2")

        client = _make_sync_client(callbacks=[CB1(), CB2()])
        client._dispatch_callback("on_request_start", RequestOptions(method="GET", url="/v1/models"))
        assert order == ["cb1", "cb2"]

    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    def test_callback_exception_does_not_propagate(self) -> None:
        class BadCallback:
            def on_request_start(self, *args: Any) -> None:
                raise RuntimeError("callback bug")

        class GoodCallback:
            def on_request_start(self, *args: Any) -> None:
                self.called = True

        good = GoodCallback()
        client = _make_sync_client(callbacks=[BadCallback(), good])
        # Should not raise
        client._dispatch_callback("on_request_start", RequestOptions(method="GET", url="/v1/models"))
        assert good.called is True

    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    def test_missing_callback_method_ignored(self) -> None:
        class PartialCallback:
            pass

        client = _make_sync_client(callbacks=[PartialCallback()])
        # Should not raise
        client._dispatch_callback("on_request_start", RequestOptions(method="GET", url="/v1/models"))
