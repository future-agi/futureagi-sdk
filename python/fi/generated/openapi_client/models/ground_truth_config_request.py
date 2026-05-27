from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ground_truth_config_request_injection_format import (
    GroundTruthConfigRequestInjectionFormat,
)
from ..models.ground_truth_config_request_mode import GroundTruthConfigRequestMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="GroundTruthConfigRequest")


@_attrs_define
class GroundTruthConfigRequest:
    """
    Attributes:
        enabled (bool | Unset):  Default: True.
        ground_truth_id (None | Unset | UUID):
        mode (GroundTruthConfigRequestMode | Unset):  Default: GroundTruthConfigRequestMode.AUTO.
        max_examples (int | Unset):
        similarity_threshold (float | Unset):
        injection_format (GroundTruthConfigRequestInjectionFormat | Unset):  Default:
            GroundTruthConfigRequestInjectionFormat.STRUCTURED.
    """

    enabled: bool | Unset = True
    ground_truth_id: None | Unset | UUID = UNSET
    mode: GroundTruthConfigRequestMode | Unset = GroundTruthConfigRequestMode.AUTO
    max_examples: int | Unset = UNSET
    similarity_threshold: float | Unset = UNSET
    injection_format: GroundTruthConfigRequestInjectionFormat | Unset = (
        GroundTruthConfigRequestInjectionFormat.STRUCTURED
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        ground_truth_id: None | str | Unset
        if isinstance(self.ground_truth_id, Unset):
            ground_truth_id = UNSET
        elif isinstance(self.ground_truth_id, UUID):
            ground_truth_id = str(self.ground_truth_id)
        else:
            ground_truth_id = self.ground_truth_id

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        max_examples = self.max_examples

        similarity_threshold = self.similarity_threshold

        injection_format: str | Unset = UNSET
        if not isinstance(self.injection_format, Unset):
            injection_format = self.injection_format.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if ground_truth_id is not UNSET:
            field_dict["ground_truth_id"] = ground_truth_id
        if mode is not UNSET:
            field_dict["mode"] = mode
        if max_examples is not UNSET:
            field_dict["max_examples"] = max_examples
        if similarity_threshold is not UNSET:
            field_dict["similarity_threshold"] = similarity_threshold
        if injection_format is not UNSET:
            field_dict["injection_format"] = injection_format

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled", UNSET)

        def _parse_ground_truth_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ground_truth_id_type_0 = UUID(data)

                return ground_truth_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        ground_truth_id = _parse_ground_truth_id(d.pop("ground_truth_id", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: GroundTruthConfigRequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = GroundTruthConfigRequestMode(_mode)

        max_examples = d.pop("max_examples", UNSET)

        similarity_threshold = d.pop("similarity_threshold", UNSET)

        _injection_format = d.pop("injection_format", UNSET)
        injection_format: GroundTruthConfigRequestInjectionFormat | Unset
        if isinstance(_injection_format, Unset):
            injection_format = UNSET
        else:
            injection_format = GroundTruthConfigRequestInjectionFormat(
                _injection_format
            )

        ground_truth_config_request = cls(
            enabled=enabled,
            ground_truth_id=ground_truth_id,
            mode=mode,
            max_examples=max_examples,
            similarity_threshold=similarity_threshold,
            injection_format=injection_format,
        )

        ground_truth_config_request.additional_properties = d
        return ground_truth_config_request

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
