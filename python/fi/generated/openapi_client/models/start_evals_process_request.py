from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StartEvalsProcessRequest")


@_attrs_define
class StartEvalsProcessRequest:
    """
    Attributes:
        user_eval_ids (list[UUID]):
        experiment_id (UUID | Unset):
        failed_only (bool | Unset):  Default: False.
    """

    user_eval_ids: list[UUID]
    experiment_id: UUID | Unset = UNSET
    failed_only: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_eval_ids = []
        for user_eval_ids_item_data in self.user_eval_ids:
            user_eval_ids_item = str(user_eval_ids_item_data)
            user_eval_ids.append(user_eval_ids_item)

        experiment_id: str | Unset = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        failed_only = self.failed_only

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_eval_ids": user_eval_ids,
            }
        )
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id
        if failed_only is not UNSET:
            field_dict["failed_only"] = failed_only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_eval_ids = []
        _user_eval_ids = d.pop("user_eval_ids")
        for user_eval_ids_item_data in _user_eval_ids:
            user_eval_ids_item = UUID(user_eval_ids_item_data)

            user_eval_ids.append(user_eval_ids_item)

        _experiment_id = d.pop("experiment_id", UNSET)
        experiment_id: UUID | Unset
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        failed_only = d.pop("failed_only", UNSET)

        start_evals_process_request = cls(
            user_eval_ids=user_eval_ids,
            experiment_id=experiment_id,
            failed_only=failed_only,
        )

        start_evals_process_request.additional_properties = d
        return start_evals_process_request

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
