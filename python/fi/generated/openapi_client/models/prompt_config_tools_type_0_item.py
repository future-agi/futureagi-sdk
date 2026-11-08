from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.prompt_config_tools_type_0_item_additional_property_type_4_type_0 import (
        PromptConfigToolsType0ItemAdditionalPropertyType4Type0,
    )


T = TypeVar("T", bound="PromptConfigToolsType0Item")


@_attrs_define
class PromptConfigToolsType0Item:
    """ """

    additional_properties: dict[
        str,
        bool
        | float
        | list[Any]
        | None
        | PromptConfigToolsType0ItemAdditionalPropertyType4Type0
        | str,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.prompt_config_tools_type_0_item_additional_property_type_4_type_0 import (
            PromptConfigToolsType0ItemAdditionalPropertyType4Type0,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, list):
                field_dict[prop_name] = prop

            elif isinstance(
                prop, PromptConfigToolsType0ItemAdditionalPropertyType4Type0
            ):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_config_tools_type_0_item_additional_property_type_4_type_0 import (
            PromptConfigToolsType0ItemAdditionalPropertyType4Type0,
        )

        d = dict(src_dict)
        prompt_config_tools_type_0_item = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                bool
                | float
                | list[Any]
                | None
                | PromptConfigToolsType0ItemAdditionalPropertyType4Type0
                | str
            ):
                if data is None:
                    return data
                try:
                    if not isinstance(data, list):
                        raise TypeError()
                    additional_property_type_3 = cast(list[Any], data)

                    return additional_property_type_3
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_4_type_0 = PromptConfigToolsType0ItemAdditionalPropertyType4Type0.from_dict(
                        data
                    )

                    return additional_property_type_4_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(
                    bool
                    | float
                    | list[Any]
                    | None
                    | PromptConfigToolsType0ItemAdditionalPropertyType4Type0
                    | str,
                    data,
                )

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        prompt_config_tools_type_0_item.additional_properties = additional_properties
        return prompt_config_tools_type_0_item

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> (
        bool
        | float
        | list[Any]
        | None
        | PromptConfigToolsType0ItemAdditionalPropertyType4Type0
        | str
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: bool
        | float
        | list[Any]
        | None
        | PromptConfigToolsType0ItemAdditionalPropertyType4Type0
        | str,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
