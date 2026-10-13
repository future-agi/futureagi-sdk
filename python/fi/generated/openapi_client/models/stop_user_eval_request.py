from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StopUserEvalRequest")


@_attrs_define
class StopUserEvalRequest:
    """
    Attributes:
        experiment_id (UUID | Unset):
    """

    experiment_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_id: str | Unset = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _experiment_id = d.pop("experiment_id", UNSET)
        experiment_id: UUID | Unset
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        stop_user_eval_request = cls(
            experiment_id=experiment_id,
        )

        stop_user_eval_request.additional_properties = d
        return stop_user_eval_request

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
