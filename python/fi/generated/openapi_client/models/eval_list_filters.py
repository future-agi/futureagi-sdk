from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_list_filters_eval_type_item import EvalListFiltersEvalTypeItem
from ..models.eval_list_filters_output_type_item import EvalListFiltersOutputTypeItem
from ..models.eval_list_filters_template_type_item import (
    EvalListFiltersTemplateTypeItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalListFilters")


@_attrs_define
class EvalListFilters:
    """
    Attributes:
        eval_type (list[EvalListFiltersEvalTypeItem] | Unset):
        output_type (list[EvalListFiltersOutputTypeItem] | Unset):
        template_type (list[EvalListFiltersTemplateTypeItem] | Unset):
        tags (list[str] | Unset):
        created_by (list[str] | Unset):
        names (list[str] | Unset):
    """

    eval_type: list[EvalListFiltersEvalTypeItem] | Unset = UNSET
    output_type: list[EvalListFiltersOutputTypeItem] | Unset = UNSET
    template_type: list[EvalListFiltersTemplateTypeItem] | Unset = UNSET
    tags: list[str] | Unset = UNSET
    created_by: list[str] | Unset = UNSET
    names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_type: list[str] | Unset = UNSET
        if not isinstance(self.eval_type, Unset):
            eval_type = []
            for eval_type_item_data in self.eval_type:
                eval_type_item = eval_type_item_data.value
                eval_type.append(eval_type_item)

        output_type: list[str] | Unset = UNSET
        if not isinstance(self.output_type, Unset):
            output_type = []
            for output_type_item_data in self.output_type:
                output_type_item = output_type_item_data.value
                output_type.append(output_type_item)

        template_type: list[str] | Unset = UNSET
        if not isinstance(self.template_type, Unset):
            template_type = []
            for template_type_item_data in self.template_type:
                template_type_item = template_type_item_data.value
                template_type.append(template_type_item)

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        created_by: list[str] | Unset = UNSET
        if not isinstance(self.created_by, Unset):
            created_by = self.created_by

        names: list[str] | Unset = UNSET
        if not isinstance(self.names, Unset):
            names = self.names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if template_type is not UNSET:
            field_dict["template_type"] = template_type
        if tags is not UNSET:
            field_dict["tags"] = tags
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if names is not UNSET:
            field_dict["names"] = names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _eval_type = d.pop("eval_type", UNSET)
        eval_type: list[EvalListFiltersEvalTypeItem] | Unset = UNSET
        if _eval_type is not UNSET:
            eval_type = []
            for eval_type_item_data in _eval_type:
                eval_type_item = EvalListFiltersEvalTypeItem(eval_type_item_data)

                eval_type.append(eval_type_item)

        _output_type = d.pop("output_type", UNSET)
        output_type: list[EvalListFiltersOutputTypeItem] | Unset = UNSET
        if _output_type is not UNSET:
            output_type = []
            for output_type_item_data in _output_type:
                output_type_item = EvalListFiltersOutputTypeItem(output_type_item_data)

                output_type.append(output_type_item)

        _template_type = d.pop("template_type", UNSET)
        template_type: list[EvalListFiltersTemplateTypeItem] | Unset = UNSET
        if _template_type is not UNSET:
            template_type = []
            for template_type_item_data in _template_type:
                template_type_item = EvalListFiltersTemplateTypeItem(
                    template_type_item_data
                )

                template_type.append(template_type_item)

        tags = cast(list[str], d.pop("tags", UNSET))

        created_by = cast(list[str], d.pop("created_by", UNSET))

        names = cast(list[str], d.pop("names", UNSET))

        eval_list_filters = cls(
            eval_type=eval_type,
            output_type=output_type,
            template_type=template_type,
            tags=tags,
            created_by=created_by,
            names=names,
        )

        eval_list_filters.additional_properties = d
        return eval_list_filters

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
