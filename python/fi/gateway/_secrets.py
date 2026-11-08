"""Opaque client state for repr-based diagnostics, not an introspection boundary."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")
_REDACTED = "[REDACTED]"


class _Secret(Generic[T]):
    """Keep a value behind an explicit accessor; never serialize it implicitly.

    Copies keep the same in-process value (including live caller configuration).
    Pickling is intentionally lossy: only the redaction marker is serialized.
    """

    __slots__ = ("__value",)

    def __init__(self, value: T) -> None:
        self.__value = value

    @classmethod
    def hold(cls, value: T | _Secret[T]) -> _Secret[T]:
        return value if isinstance(value, cls) else cls(value)

    def get(self) -> T:
        return self.__value

    def __repr__(self) -> str:
        return _REDACTED

    def __str__(self) -> str:
        return _REDACTED

    def __format__(self, format_spec: str) -> str:
        return _REDACTED

    def __reduce__(self) -> tuple[Any, tuple[str]]:
        return str, (_REDACTED,)

    def __copy__(self) -> _Secret[T]:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> _Secret[T]:
        return self

    def key_preview(self: _Secret[str]) -> str:
        """Preserve the released client repr without a raw key local."""
        if len(self.__value) > 14:
            return f"{self.__value[:10]}...{self.__value[-4:]}"
        return "***"


def client_key(value: str | _Secret[str | None] | None) -> _Secret[str]:
    from fi.gateway._env import resolve_api_key

    value = _Secret.hold(value)
    # Resolve and recheck without leaving a raw argument in this frame.
    return _Secret(resolve_api_key(value.get()))
