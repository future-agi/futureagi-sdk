from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define

T = TypeVar("T", bound="DiffCaseRequest")


@_attrs_define
class DiffCaseRequest:
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        diff_case_request = cls(
            example_id=example_id,
            trial_number=trial_number,
        )

        return diff_case_request
