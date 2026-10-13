from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_template_version_create_request_config_snapshot import (
        EvalTemplateVersionCreateRequestConfigSnapshot,
    )


T = TypeVar("T", bound="EvalTemplateVersionCreateRequest")


@_attrs_define
class EvalTemplateVersionCreateRequest:
    """
    Attributes:
        criteria (None | str | Unset):
        model (None | str | Unset):
        config_snapshot (EvalTemplateVersionCreateRequestConfigSnapshot | Unset):
    """

    criteria: None | str | Unset = UNSET
    model: None | str | Unset = UNSET
    config_snapshot: EvalTemplateVersionCreateRequestConfigSnapshot | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        criteria: None | str | Unset
        if isinstance(self.criteria, Unset):
            criteria = UNSET
        else:
            criteria = self.criteria

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        config_snapshot: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_snapshot, Unset):
            config_snapshot = self.config_snapshot.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if criteria is not UNSET:
            field_dict["criteria"] = criteria
        if model is not UNSET:
            field_dict["model"] = model
        if config_snapshot is not UNSET:
            field_dict["config_snapshot"] = config_snapshot

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_version_create_request_config_snapshot import (
            EvalTemplateVersionCreateRequestConfigSnapshot,
        )

        d = dict(src_dict)

        def _parse_criteria(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        criteria = _parse_criteria(d.pop("criteria", UNSET))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _config_snapshot = d.pop("config_snapshot", UNSET)
        config_snapshot: EvalTemplateVersionCreateRequestConfigSnapshot | Unset
        if isinstance(_config_snapshot, Unset):
            config_snapshot = UNSET
        else:
            config_snapshot = EvalTemplateVersionCreateRequestConfigSnapshot.from_dict(
                _config_snapshot
            )

        eval_template_version_create_request = cls(
            criteria=criteria,
            model=model,
            config_snapshot=config_snapshot,
        )

        eval_template_version_create_request.additional_properties = d
        return eval_template_version_create_request

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
