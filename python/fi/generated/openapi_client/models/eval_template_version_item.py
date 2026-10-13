from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_template_version_item_config_snapshot import (
        EvalTemplateVersionItemConfigSnapshot,
    )


T = TypeVar("T", bound="EvalTemplateVersionItem")


@_attrs_define
class EvalTemplateVersionItem:
    """
    Attributes:
        id (UUID):
        version_number (int):
        is_default (bool):
        criteria (str | Unset):
        model (str | Unset):
        config_snapshot (EvalTemplateVersionItemConfigSnapshot | Unset):
        created_by_name (str | Unset):
        created_at (str | Unset):
    """

    id: UUID
    version_number: int
    is_default: bool
    criteria: str | Unset = UNSET
    model: str | Unset = UNSET
    config_snapshot: EvalTemplateVersionItemConfigSnapshot | Unset = UNSET
    created_by_name: str | Unset = UNSET
    created_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        version_number = self.version_number

        is_default = self.is_default

        criteria = self.criteria

        model = self.model

        config_snapshot: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_snapshot, Unset):
            config_snapshot = self.config_snapshot.to_dict()

        created_by_name = self.created_by_name

        created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "version_number": version_number,
                "is_default": is_default,
            }
        )
        if criteria is not UNSET:
            field_dict["criteria"] = criteria
        if model is not UNSET:
            field_dict["model"] = model
        if config_snapshot is not UNSET:
            field_dict["config_snapshot"] = config_snapshot
        if created_by_name is not UNSET:
            field_dict["created_by_name"] = created_by_name
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_version_item_config_snapshot import (
            EvalTemplateVersionItemConfigSnapshot,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        version_number = d.pop("version_number")

        is_default = d.pop("is_default")

        criteria = d.pop("criteria", UNSET)

        model = d.pop("model", UNSET)

        _config_snapshot = d.pop("config_snapshot", UNSET)
        config_snapshot: EvalTemplateVersionItemConfigSnapshot | Unset
        if isinstance(_config_snapshot, Unset):
            config_snapshot = UNSET
        else:
            config_snapshot = EvalTemplateVersionItemConfigSnapshot.from_dict(
                _config_snapshot
            )

        created_by_name = d.pop("created_by_name", UNSET)

        created_at = d.pop("created_at", UNSET)

        eval_template_version_item = cls(
            id=id,
            version_number=version_number,
            is_default=is_default,
            criteria=criteria,
            model=model,
            config_snapshot=config_snapshot,
            created_by_name=created_by_name,
            created_at=created_at,
        )

        eval_template_version_item.additional_properties = d
        return eval_template_version_item

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
