from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.release_gate_blocker_reason import ReleaseGateBlockerReason

T = TypeVar("T", bound="ReleaseGateBlocker")


@_attrs_define
class ReleaseGateBlocker:
    """
    Attributes:
        example_id (None | UUID):
        trial_number (int | None):
        reason (ReleaseGateBlockerReason):
    """

    example_id: None | UUID
    trial_number: int | None
    reason: ReleaseGateBlockerReason
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example_id: None | str
        if isinstance(self.example_id, UUID):
            example_id = str(self.example_id)
        else:
            example_id = self.example_id

        trial_number: int | None
        trial_number = self.trial_number

        reason = self.reason.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
                "reason": reason,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_example_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                example_id_type_0 = UUID(data)

                return example_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        example_id = _parse_example_id(d.pop("example_id"))

        def _parse_trial_number(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        trial_number = _parse_trial_number(d.pop("trial_number"))

        reason = ReleaseGateBlockerReason(d.pop("reason"))

        release_gate_blocker = cls(
            example_id=example_id,
            trial_number=trial_number,
            reason=reason,
        )

        release_gate_blocker.additional_properties = d
        return release_gate_blocker

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
