"""Shared validation/access warnings for published model field spellings."""
from collections.abc import Mapping
from threading import Lock
import warnings

from pydantic import AliasChoices, BaseModel, model_validator

_seen: set[tuple[str, str]] = set()
_lock = Lock()


def _warn_alias(old: str, new: str) -> None:
    with _lock:
        if (old, new) in _seen:
            return
        _seen.add((old, new))
    warnings.warn(
        f"{old} is deprecated; use {new} instead.",
        DeprecationWarning,
        stacklevel=4,
    )


class LegacyFieldsModel(BaseModel):
    """Keep each subclass's extra policy and prefer its first validation alias.

    A legacy input or readable legacy field warns once per process per alias.
    AliasChoices validates inputs, including nested models and JSON. The warning
    layer never discards or coerces values.
    """

    @model_validator(mode="before")
    @classmethod
    def _warn_legacy_inputs(cls, value):
        if isinstance(value, Mapping):
            for field in cls.model_fields.values():
                aliases = field.validation_alias
                if isinstance(aliases, AliasChoices):
                    for old in aliases.choices[1:]:
                        if isinstance(old, str) and old in value:
                            _warn_alias(old, aliases.choices[0])
        return value

    def __getattribute__(self, name):
        field = type(self).model_fields.get(name)
        if field is not None:
            aliases = field.validation_alias
            if isinstance(aliases, AliasChoices) and name != aliases.choices[0]:
                _warn_alias(name, aliases.choices[0])
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        field = type(self).model_fields.get(name)
        if field is not None:
            aliases = field.validation_alias
            if isinstance(aliases, AliasChoices) and name != aliases.choices[0]:
                _warn_alias(name, aliases.choices[0])
        super().__setattr__(name, value)


def legacy_property(old: str, canonical: str) -> property:
    """Expose a deprecated read/write alias without changing model metadata."""
    def get(self):
        _warn_alias(old, canonical)
        return getattr(self, canonical)

    def set_value(self, value):
        _warn_alias(old, canonical)
        setattr(self, canonical, value)

    return property(get, set_value, doc=f"Deprecated alias of {canonical}.")


def preferred_property(storage: str, name: str) -> property:
    """Expose a snake-case view without warning through a legacy storage field."""
    def get(self):
        return object.__getattribute__(self, storage)

    def set_value(self, value):
        BaseModel.__setattr__(self, storage, value)

    return property(get, set_value, doc=f"Preferred spelling of the deprecated {storage} field: {name}.")
