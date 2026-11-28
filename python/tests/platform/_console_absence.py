"""Explicit Console absence oracle shared by each retained hidden scenario."""
import pytest


def assert_console_absent(subject):
    assert subject.row.get("public_absence") == {
        "py": ["client.agents", "client.environments"],
        "ts": ["client.agents", "client.environments"],
    }
    assert not hasattr(subject.client, "agents")
    assert not hasattr(subject.client, "environments")
    with pytest.raises(AttributeError, match="agents"):
        getattr(subject.client, "agents")
    with pytest.raises(AttributeError, match="environments"):
        getattr(subject.client, "environments")
    assert subject.setup_requests == []
    assert subject.handles == {}
