"""Validate selected generated responses before tolerant Pydantic field coercion."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any, ClassVar, FrozenSet

from pydantic import BaseModel, ConfigDict, ValidationInfo, model_validator

RESPONSE_CONFIG = ConfigDict(extra="allow", populate_by_name=True, protected_namespaces=(), coerce_numbers_to_str=True)


@lru_cache(maxsize=None)
def _validator(name: str):
    # Do not load jsonschema or the projected wire definitions for tolerant reads.
    from jsonschema import Draft7Validator

    definitions = json.loads(files(__package__).joinpath("_wire_definitions.json").read_bytes())
    return Draft7Validator({"$ref": f"#/definitions/{name}", "definitions": definitions})


class WireResponse(BaseModel):
    model_config = RESPONSE_CONFIG
    __required__: ClassVar[FrozenSet[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def _check_wire(cls, value: Any, info: ValidationInfo) -> Any:
        if info.context and info.context.get("strict"):
            error = next(_validator(cls.__name__).iter_errors(value), None)
            if error is not None:
                # A schema location is sufficient; do not include response values.
                raise ValueError(f"response violates {error.validator} at {error.json_path}")
        return value
