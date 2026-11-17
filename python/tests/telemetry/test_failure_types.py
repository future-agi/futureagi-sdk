import httpx
import pytest

from fi.context.snapshot import ResolutionExpiredError
from fi.platform._errors import PermissionDeniedError


@pytest.mark.parametrize("error,kind", [
    (ResolutionExpiredError("private lease"), "lease"),
    (PermissionDeniedError("private authorization detail", response=httpx.Response(403), body={}), "authorization"),
    (FileNotFoundError("private local path"), "not_found"),
    (RuntimeError("private exception text"), "other"),
])
def test_errors_preserve_application_exception_without_identity(tracing, make_snapshot, error, kind, caplog):
    tracer, exporter, _ = tracing
    snapshot, source = make_snapshot()
    source.error = error
    with tracer.start_as_current_span("request"):
        with pytest.raises(type(error)) as raised:
            snapshot.read_file("SKILL.md")
        assert raised.value is error
    load = next(s for s in exporter.get_finished_spans() if s.name == "skill.load")
    assert load.attributes["error.type"] == kind
    assert load.status.status_code.name == "ERROR"
    assert not any(key in load.attributes for key in ("fi.skill.id", "fi.skill.version_id", "fi.skill.digest"))
    assert not load.events
    assert "private" not in str(load.attributes)
    assert "private" not in caplog.text
