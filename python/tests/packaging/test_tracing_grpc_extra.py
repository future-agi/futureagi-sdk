"""Keep the OTLP gRPC exporter out of the base distribution."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def test_grpc_exporter_is_only_a_tracing_extra():
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with project.open("rb") as stream:
        poetry = tomllib.load(stream)["tool"]["poetry"]

    name = "opentelemetry-exporter-otlp-proto-grpc"
    assert poetry["dependencies"][name]["optional"] is True
    assert {extra for extra, packages in poetry["extras"].items() if name in packages} == {"tracing-grpc"}
