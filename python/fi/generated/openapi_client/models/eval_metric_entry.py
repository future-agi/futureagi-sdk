from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_metric_entry_composite_weight_overrides import (
        EvalMetricEntryCompositeWeightOverrides,
    )
    from ..models.eval_metric_entry_config import EvalMetricEntryConfig


T = TypeVar("T", bound="EvalMetricEntry")


@_attrs_define
class EvalMetricEntry:
    """
    Attributes:
        template_id (UUID):
        name (str):
        config (EvalMetricEntryConfig):
        id (None | Unset | UUID):
        model (str | Unset):  Default: ''.
        error_localizer (bool | Unset):  Default: False.
        kb_id (None | Unset | UUID):
        composite_weight_overrides (EvalMetricEntryCompositeWeightOverrides | Unset):
    """

    template_id: UUID
    name: str
    config: EvalMetricEntryConfig
    id: None | Unset | UUID = UNSET
    model: str | Unset = ""
    error_localizer: bool | Unset = False
    kb_id: None | Unset | UUID = UNSET
    composite_weight_overrides: EvalMetricEntryCompositeWeightOverrides | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = str(self.template_id)

        name = self.name

        config = self.config.to_dict()

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        model = self.model

        error_localizer = self.error_localizer

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        composite_weight_overrides: dict[str, Any] | Unset = UNSET
        if not isinstance(self.composite_weight_overrides, Unset):
            composite_weight_overrides = self.composite_weight_overrides.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "name": name,
                "config": config,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if model is not UNSET:
            field_dict["model"] = model
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if composite_weight_overrides is not UNSET:
            field_dict["composite_weight_overrides"] = composite_weight_overrides

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_metric_entry_composite_weight_overrides import (
            EvalMetricEntryCompositeWeightOverrides,
        )
        from ..models.eval_metric_entry_config import EvalMetricEntryConfig

        d = dict(src_dict)
        template_id = UUID(d.pop("template_id"))

        name = d.pop("name")

        config = EvalMetricEntryConfig.from_dict(d.pop("config"))

        def _parse_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        id = _parse_id(d.pop("id", UNSET))

        model = d.pop("model", UNSET)

        error_localizer = d.pop("error_localizer", UNSET)

        def _parse_kb_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                kb_id_type_0 = UUID(data)

                return kb_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        kb_id = _parse_kb_id(d.pop("kb_id", UNSET))

        _composite_weight_overrides = d.pop("composite_weight_overrides", UNSET)
        composite_weight_overrides: EvalMetricEntryCompositeWeightOverrides | Unset
        if isinstance(_composite_weight_overrides, Unset):
            composite_weight_overrides = UNSET
        else:
            composite_weight_overrides = (
                EvalMetricEntryCompositeWeightOverrides.from_dict(
                    _composite_weight_overrides
                )
            )

        eval_metric_entry = cls(
            template_id=template_id,
            name=name,
            config=config,
            id=id,
            model=model,
            error_localizer=error_localizer,
            kb_id=kb_id,
            composite_weight_overrides=composite_weight_overrides,
        )

        eval_metric_entry.additional_properties = d
        return eval_metric_entry

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
