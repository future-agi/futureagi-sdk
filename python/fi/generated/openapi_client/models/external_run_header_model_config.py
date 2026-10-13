from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.external_run_header_model_config_additional_property_type_4_type_0 import (
        ExternalRunHeaderModelConfigAdditionalPropertyType4Type0,
    )


T = TypeVar("T", bound="ExternalRunHeaderModelConfig")


@_attrs_define
class ExternalRunHeaderModelConfig:
    """ """

    additional_properties: dict[
        str,
        bool
        | ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
        | float
        | list[Any]
        | None
        | str,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.external_run_header_model_config_additional_property_type_4_type_0 import (
            ExternalRunHeaderModelConfigAdditionalPropertyType4Type0,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, list):
                field_dict[prop_name] = prop

            elif isinstance(
                prop, ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
            ):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_header_model_config_additional_property_type_4_type_0 import (
            ExternalRunHeaderModelConfigAdditionalPropertyType4Type0,
        )

        d = dict(src_dict)
        external_run_header_model_config = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                bool
                | ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
                | float
                | list[Any]
                | None
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
                    additional_property_type_4_type_0 = ExternalRunHeaderModelConfigAdditionalPropertyType4Type0.from_dict(
                        data
                    )

                    return additional_property_type_4_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(
                    bool
                    | ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
                    | float
                    | list[Any]
                    | None
                    | str,
                    data,
                )

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        external_run_header_model_config.additional_properties = additional_properties
        return external_run_header_model_config

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> (
        bool
        | ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
        | float
        | list[Any]
        | None
        | str
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: bool
        | ExternalRunHeaderModelConfigAdditionalPropertyType4Type0
        | float
        | list[Any]
        | None
        | str,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
