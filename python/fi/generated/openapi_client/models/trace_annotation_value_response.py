from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_annotation_value_response_annotation_value import (
        TraceAnnotationValueResponseAnnotationValue,
    )
    from ..models.trace_annotation_value_response_settings import (
        TraceAnnotationValueResponseSettings,
    )


T = TypeVar("T", bound="TraceAnnotationValueResponse")


@_attrs_define
class TraceAnnotationValueResponse:
    """
    Attributes:
        id (UUID):
        annotation_label_name (str):
        annotation_value (TraceAnnotationValueResponseAnnotationValue):
        annotation_label_id (UUID):
        annotation_type (str):
        annotator (None | str | Unset):
        annotator_id (None | Unset | UUID):
        updated_by (None | str | Unset):
        updated_at (datetime.datetime | None | Unset):
        settings (TraceAnnotationValueResponseSettings | Unset):
    """

    id: UUID
    annotation_label_name: str
    annotation_value: TraceAnnotationValueResponseAnnotationValue
    annotation_label_id: UUID
    annotation_type: str
    annotator: None | str | Unset = UNSET
    annotator_id: None | Unset | UUID = UNSET
    updated_by: None | str | Unset = UNSET
    updated_at: datetime.datetime | None | Unset = UNSET
    settings: TraceAnnotationValueResponseSettings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        annotation_label_name = self.annotation_label_name

        annotation_value = self.annotation_value.to_dict()

        annotation_label_id = str(self.annotation_label_id)

        annotation_type = self.annotation_type

        annotator: None | str | Unset
        if isinstance(self.annotator, Unset):
            annotator = UNSET
        else:
            annotator = self.annotator

        annotator_id: None | str | Unset
        if isinstance(self.annotator_id, Unset):
            annotator_id = UNSET
        elif isinstance(self.annotator_id, UUID):
            annotator_id = str(self.annotator_id)
        else:
            annotator_id = self.annotator_id

        updated_by: None | str | Unset
        if isinstance(self.updated_by, Unset):
            updated_by = UNSET
        else:
            updated_by = self.updated_by

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "annotation_label_name": annotation_label_name,
                "annotation_value": annotation_value,
                "annotation_label_id": annotation_label_id,
                "annotation_type": annotation_type,
            }
        )
        if annotator is not UNSET:
            field_dict["annotator"] = annotator
        if annotator_id is not UNSET:
            field_dict["annotator_id"] = annotator_id
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_annotation_value_response_annotation_value import (
            TraceAnnotationValueResponseAnnotationValue,
        )
        from ..models.trace_annotation_value_response_settings import (
            TraceAnnotationValueResponseSettings,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        annotation_label_name = d.pop("annotation_label_name")

        annotation_value = TraceAnnotationValueResponseAnnotationValue.from_dict(
            d.pop("annotation_value")
        )

        annotation_label_id = UUID(d.pop("annotation_label_id"))

        annotation_type = d.pop("annotation_type")

        def _parse_annotator(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        annotator = _parse_annotator(d.pop("annotator", UNSET))

        def _parse_annotator_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                annotator_id_type_0 = UUID(data)

                return annotator_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        annotator_id = _parse_annotator_id(d.pop("annotator_id", UNSET))

        def _parse_updated_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_by = _parse_updated_by(d.pop("updated_by", UNSET))

        def _parse_updated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        _settings = d.pop("settings", UNSET)
        settings: TraceAnnotationValueResponseSettings | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = TraceAnnotationValueResponseSettings.from_dict(_settings)

        trace_annotation_value_response = cls(
            id=id,
            annotation_label_name=annotation_label_name,
            annotation_value=annotation_value,
            annotation_label_id=annotation_label_id,
            annotation_type=annotation_type,
            annotator=annotator,
            annotator_id=annotator_id,
            updated_by=updated_by,
            updated_at=updated_at,
            settings=settings,
        )

        trace_annotation_value_response.additional_properties = d
        return trace_annotation_value_response

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
