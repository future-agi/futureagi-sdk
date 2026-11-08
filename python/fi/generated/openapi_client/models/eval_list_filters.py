from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_list_filters_eval_type_item import EvalListFiltersEvalTypeItem
from ..models.eval_list_filters_eval_type_not_item import EvalListFiltersEvalTypeNotItem
from ..models.eval_list_filters_output_type_item import EvalListFiltersOutputTypeItem
from ..models.eval_list_filters_output_type_not_item import (
    EvalListFiltersOutputTypeNotItem,
)
from ..models.eval_list_filters_template_type_item import (
    EvalListFiltersTemplateTypeItem,
)
from ..models.eval_list_filters_template_type_not_item import (
    EvalListFiltersTemplateTypeNotItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalListFilters")


@_attrs_define
class EvalListFilters:
    """
    Attributes:
        eval_type (list[EvalListFiltersEvalTypeItem] | Unset):
        eval_type_not (list[EvalListFiltersEvalTypeNotItem] | Unset):
        output_type (list[EvalListFiltersOutputTypeItem] | Unset):
        output_type_not (list[EvalListFiltersOutputTypeNotItem] | Unset):
        template_type (list[EvalListFiltersTemplateTypeItem] | Unset):
        template_type_not (list[EvalListFiltersTemplateTypeNotItem] | Unset):
        tags (list[str] | Unset):
        tags_not (list[str] | Unset):
        created_by (list[str] | Unset):
        created_by_not (list[str] | Unset):
        names (list[str] | Unset):
        names_not (list[str] | Unset):
    """

    eval_type: list[EvalListFiltersEvalTypeItem] | Unset = UNSET
    eval_type_not: list[EvalListFiltersEvalTypeNotItem] | Unset = UNSET
    output_type: list[EvalListFiltersOutputTypeItem] | Unset = UNSET
    output_type_not: list[EvalListFiltersOutputTypeNotItem] | Unset = UNSET
    template_type: list[EvalListFiltersTemplateTypeItem] | Unset = UNSET
    template_type_not: list[EvalListFiltersTemplateTypeNotItem] | Unset = UNSET
    tags: list[str] | Unset = UNSET
    tags_not: list[str] | Unset = UNSET
    created_by: list[str] | Unset = UNSET
    created_by_not: list[str] | Unset = UNSET
    names: list[str] | Unset = UNSET
    names_not: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_type: list[str] | Unset = UNSET
        if not isinstance(self.eval_type, Unset):
            eval_type = []
            for eval_type_item_data in self.eval_type:
                eval_type_item = eval_type_item_data.value
                eval_type.append(eval_type_item)

        eval_type_not: list[str] | Unset = UNSET
        if not isinstance(self.eval_type_not, Unset):
            eval_type_not = []
            for eval_type_not_item_data in self.eval_type_not:
                eval_type_not_item = eval_type_not_item_data.value
                eval_type_not.append(eval_type_not_item)

        output_type: list[str] | Unset = UNSET
        if not isinstance(self.output_type, Unset):
            output_type = []
            for output_type_item_data in self.output_type:
                output_type_item = output_type_item_data.value
                output_type.append(output_type_item)

        output_type_not: list[str] | Unset = UNSET
        if not isinstance(self.output_type_not, Unset):
            output_type_not = []
            for output_type_not_item_data in self.output_type_not:
                output_type_not_item = output_type_not_item_data.value
                output_type_not.append(output_type_not_item)

        template_type: list[str] | Unset = UNSET
        if not isinstance(self.template_type, Unset):
            template_type = []
            for template_type_item_data in self.template_type:
                template_type_item = template_type_item_data.value
                template_type.append(template_type_item)

        template_type_not: list[str] | Unset = UNSET
        if not isinstance(self.template_type_not, Unset):
            template_type_not = []
            for template_type_not_item_data in self.template_type_not:
                template_type_not_item = template_type_not_item_data.value
                template_type_not.append(template_type_not_item)

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        tags_not: list[str] | Unset = UNSET
        if not isinstance(self.tags_not, Unset):
            tags_not = self.tags_not

        created_by: list[str] | Unset = UNSET
        if not isinstance(self.created_by, Unset):
            created_by = self.created_by

        created_by_not: list[str] | Unset = UNSET
        if not isinstance(self.created_by_not, Unset):
            created_by_not = self.created_by_not

        names: list[str] | Unset = UNSET
        if not isinstance(self.names, Unset):
            names = self.names

        names_not: list[str] | Unset = UNSET
        if not isinstance(self.names_not, Unset):
            names_not = self.names_not

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if eval_type_not is not UNSET:
            field_dict["eval_type_not"] = eval_type_not
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if output_type_not is not UNSET:
            field_dict["output_type_not"] = output_type_not
        if template_type is not UNSET:
            field_dict["template_type"] = template_type
        if template_type_not is not UNSET:
            field_dict["template_type_not"] = template_type_not
        if tags is not UNSET:
            field_dict["tags"] = tags
        if tags_not is not UNSET:
            field_dict["tags_not"] = tags_not
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_by_not is not UNSET:
            field_dict["created_by_not"] = created_by_not
        if names is not UNSET:
            field_dict["names"] = names
        if names_not is not UNSET:
            field_dict["names_not"] = names_not

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

        _eval_type_not = d.pop("eval_type_not", UNSET)
        eval_type_not: list[EvalListFiltersEvalTypeNotItem] | Unset = UNSET
        if _eval_type_not is not UNSET:
            eval_type_not = []
            for eval_type_not_item_data in _eval_type_not:
                eval_type_not_item = EvalListFiltersEvalTypeNotItem(
                    eval_type_not_item_data
                )

                eval_type_not.append(eval_type_not_item)

        _output_type = d.pop("output_type", UNSET)
        output_type: list[EvalListFiltersOutputTypeItem] | Unset = UNSET
        if _output_type is not UNSET:
            output_type = []
            for output_type_item_data in _output_type:
                output_type_item = EvalListFiltersOutputTypeItem(output_type_item_data)

                output_type.append(output_type_item)

        _output_type_not = d.pop("output_type_not", UNSET)
        output_type_not: list[EvalListFiltersOutputTypeNotItem] | Unset = UNSET
        if _output_type_not is not UNSET:
            output_type_not = []
            for output_type_not_item_data in _output_type_not:
                output_type_not_item = EvalListFiltersOutputTypeNotItem(
                    output_type_not_item_data
                )

                output_type_not.append(output_type_not_item)

        _template_type = d.pop("template_type", UNSET)
        template_type: list[EvalListFiltersTemplateTypeItem] | Unset = UNSET
        if _template_type is not UNSET:
            template_type = []
            for template_type_item_data in _template_type:
                template_type_item = EvalListFiltersTemplateTypeItem(
                    template_type_item_data
                )

                template_type.append(template_type_item)

        _template_type_not = d.pop("template_type_not", UNSET)
        template_type_not: list[EvalListFiltersTemplateTypeNotItem] | Unset = UNSET
        if _template_type_not is not UNSET:
            template_type_not = []
            for template_type_not_item_data in _template_type_not:
                template_type_not_item = EvalListFiltersTemplateTypeNotItem(
                    template_type_not_item_data
                )

                template_type_not.append(template_type_not_item)

        tags = cast(list[str], d.pop("tags", UNSET))

        tags_not = cast(list[str], d.pop("tags_not", UNSET))

        created_by = cast(list[str], d.pop("created_by", UNSET))

        created_by_not = cast(list[str], d.pop("created_by_not", UNSET))

        names = cast(list[str], d.pop("names", UNSET))

        names_not = cast(list[str], d.pop("names_not", UNSET))

        eval_list_filters = cls(
            eval_type=eval_type,
            eval_type_not=eval_type_not,
            output_type=output_type,
            output_type_not=output_type_not,
            template_type=template_type,
            template_type_not=template_type_not,
            tags=tags,
            tags_not=tags_not,
            created_by=created_by,
            created_by_not=created_by_not,
            names=names,
            names_not=names_not,
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
