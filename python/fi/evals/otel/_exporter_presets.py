"""The read-only exporter presets of ``fi.evals.otel.config``."""

import copy
from collections.abc import Mapping
from typing import Any, Dict, Iterator


class ReadOnlyPresets(Mapping):
    """A read-only view of the exporter presets whose every read returns a fresh deep copy of the template, so the
    headers and options one caller adds stay with that caller's configuration."""

    def __init__(self, presets: Dict[str, Any]) -> None:
        self._presets = presets

    def __getitem__(self, name: str) -> Any:
        return copy.deepcopy(self._presets[name])

    def __iter__(self) -> Iterator[str]:
        return iter(self._presets)

    def __len__(self) -> int:
        return len(self._presets)

    def __repr__(self) -> str:
        return f"EXPORTER_PRESETS({list(self._presets)!r})"
