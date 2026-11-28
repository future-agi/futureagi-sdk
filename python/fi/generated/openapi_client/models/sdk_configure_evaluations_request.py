from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.configure_evaluations import ConfigureEvaluations
    from ..models.sdk_configure_evaluations_request_additional_property import (
        SDKConfigureEvaluationsRequestAdditionalProperty,
    )


T = TypeVar("T", bound="SDKConfigureEvaluationsRequest")


@_attrs_define
class SDKConfigureEvaluationsRequest:
    """
    Attributes:
        eval_config (ConfigureEvaluations):
        platform (str):
        custom_eval_name (None | str | Unset):
    """

    eval_config: ConfigureEvaluations
    platform: str
    custom_eval_name: None | str | Unset = UNSET
    additional_properties: dict[
        str, SDKConfigureEvaluationsRequestAdditionalProperty
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_config = self.eval_config.to_dict()

        platform = self.platform

        custom_eval_name: None | str | Unset
        if isinstance(self.custom_eval_name, Unset):
            custom_eval_name = UNSET
        else:
            custom_eval_name = self.custom_eval_name

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        field_dict.update(
            {
                "eval_config": eval_config,
                "platform": platform,
            }
        )
        if custom_eval_name is not UNSET:
            field_dict["custom_eval_name"] = custom_eval_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.configure_evaluations import ConfigureEvaluations
        from ..models.sdk_configure_evaluations_request_additional_property import (
            SDKConfigureEvaluationsRequestAdditionalProperty,
        )

        d = dict(src_dict)
        eval_config = ConfigureEvaluations.from_dict(d.pop("eval_config"))

        platform = d.pop("platform")

        def _parse_custom_eval_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        custom_eval_name = _parse_custom_eval_name(d.pop("custom_eval_name", UNSET))

        sdk_configure_evaluations_request = cls(
            eval_config=eval_config,
            platform=platform,
            custom_eval_name=custom_eval_name,
        )

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = (
                SDKConfigureEvaluationsRequestAdditionalProperty.from_dict(prop_dict)
            )

            additional_properties[prop_name] = additional_property

        sdk_configure_evaluations_request.additional_properties = additional_properties
        return sdk_configure_evaluations_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> SDKConfigureEvaluationsRequestAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(
        self, key: str, value: SDKConfigureEvaluationsRequestAdditionalProperty
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
