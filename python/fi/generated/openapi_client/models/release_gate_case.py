from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define

from ._release_gate_validation import validate_release_gate

T = TypeVar("T", bound="ReleaseGateCase")


@_attrs_define
class ReleaseGateCase:
    """
    Attributes:
        example_id (UUID):
        trial_number (int):
    """

    example_id: UUID
    trial_number: int

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        trial_number = self.trial_number

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
            }
        )

        validate_release_gate(field_dict, "ReleaseGateCase")

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        validate_release_gate(src_dict, "ReleaseGateCase")

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        release_gate_case = cls(
            example_id=example_id,
            trial_number=trial_number,
        )

        return release_gate_case
