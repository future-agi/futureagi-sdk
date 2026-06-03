from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetTraceAnnotation")


@_attrs_define
class GetTraceAnnotation:
    """
    Attributes:
        observation_span_id (None | str | Unset):
        trace_id (None | Unset | UUID):
        annotators (str | Unset): JSON-encoded UUID list.
        exclude_annotators (str | Unset): JSON-encoded UUID list.
    """

    observation_span_id: None | str | Unset = UNSET
    trace_id: None | Unset | UUID = UNSET
    annotators: str | Unset = UNSET
    exclude_annotators: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observation_span_id: None | str | Unset
        if isinstance(self.observation_span_id, Unset):
            observation_span_id = UNSET
        else:
            observation_span_id = self.observation_span_id

        trace_id: None | str | Unset
        if isinstance(self.trace_id, Unset):
            trace_id = UNSET
        elif isinstance(self.trace_id, UUID):
            trace_id = str(self.trace_id)
        else:
            trace_id = self.trace_id

        annotators = self.annotators

        exclude_annotators = self.exclude_annotators

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if observation_span_id is not UNSET:
            field_dict["observation_span_id"] = observation_span_id
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id
        if annotators is not UNSET:
            field_dict["annotators"] = annotators
        if exclude_annotators is not UNSET:
            field_dict["exclude_annotators"] = exclude_annotators

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_observation_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        observation_span_id = _parse_observation_span_id(
            d.pop("observation_span_id", UNSET)
        )

        def _parse_trace_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                trace_id_type_0 = UUID(data)

                return trace_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        trace_id = _parse_trace_id(d.pop("trace_id", UNSET))

        annotators = d.pop("annotators", UNSET)

        exclude_annotators = d.pop("exclude_annotators", UNSET)

        get_trace_annotation = cls(
            observation_span_id=observation_span_id,
            trace_id=trace_id,
            annotators=annotators,
            exclude_annotators=exclude_annotators,
        )

        get_trace_annotation.additional_properties = d
        return get_trace_annotation

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
