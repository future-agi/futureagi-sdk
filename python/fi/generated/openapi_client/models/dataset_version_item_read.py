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
    from ..models.dataset_version_item_read_expected_type_4_type_0 import (
        DatasetVersionItemReadExpectedType4Type0,
    )
    from ..models.dataset_version_item_read_input_type_4 import (
        DatasetVersionItemReadInputType4,
    )
    from ..models.dataset_version_item_read_metadata import (
        DatasetVersionItemReadMetadata,
    )


T = TypeVar("T", bound="DatasetVersionItemRead")


@_attrs_define
class DatasetVersionItemRead:
    """
    Attributes:
        id (UUID | Unset):
        example_id (UUID | Unset):
        external_id (None | str | Unset):
        input_ (bool | DatasetVersionItemReadInputType4 | float | list[Any] | str | Unset): Any non-null JSON value;
            nested nulls are allowed.
        expected (bool | DatasetVersionItemReadExpectedType4Type0 | float | list[Any] | None | str | Unset): Any valid
            JSON value.
        metadata (DatasetVersionItemReadMetadata | Unset):
        source_trace_id (str | Unset):
        source_span_id (str | Unset):
        content_hash (str | Unset):
        legacy_row (None | Unset | UUID):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
    """

    id: UUID | Unset = UNSET
    example_id: UUID | Unset = UNSET
    external_id: None | str | Unset = UNSET
    input_: (
        bool | DatasetVersionItemReadInputType4 | float | list[Any] | str | Unset
    ) = UNSET
    expected: (
        bool
        | DatasetVersionItemReadExpectedType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    metadata: DatasetVersionItemReadMetadata | Unset = UNSET
    source_trace_id: str | Unset = UNSET
    source_span_id: str | Unset = UNSET
    content_hash: str | Unset = UNSET
    legacy_row: None | Unset | UUID = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.dataset_version_item_read_expected_type_4_type_0 import (
            DatasetVersionItemReadExpectedType4Type0,
        )
        from ..models.dataset_version_item_read_input_type_4 import (
            DatasetVersionItemReadInputType4,
        )

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        example_id: str | Unset = UNSET
        if not isinstance(self.example_id, Unset):
            example_id = str(self.example_id)

        external_id: None | str | Unset
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        input_: bool | dict[str, Any] | float | list[Any] | str | Unset
        if isinstance(self.input_, Unset):
            input_ = UNSET
        elif isinstance(self.input_, list):
            input_ = self.input_

        elif isinstance(self.input_, DatasetVersionItemReadInputType4):
            input_ = self.input_.to_dict()
        else:
            input_ = self.input_

        expected: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.expected, Unset):
            expected = UNSET
        elif isinstance(self.expected, list):
            expected = self.expected

        elif isinstance(self.expected, DatasetVersionItemReadExpectedType4Type0):
            expected = self.expected.to_dict()
        else:
            expected = self.expected

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        source_trace_id = self.source_trace_id

        source_span_id = self.source_span_id

        content_hash = self.content_hash

        legacy_row: None | str | Unset
        if isinstance(self.legacy_row, Unset):
            legacy_row = UNSET
        elif isinstance(self.legacy_row, UUID):
            legacy_row = str(self.legacy_row)
        else:
            legacy_row = self.legacy_row

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if example_id is not UNSET:
            field_dict["example_id"] = example_id
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if input_ is not UNSET:
            field_dict["input"] = input_
        if expected is not UNSET:
            field_dict["expected"] = expected
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if source_trace_id is not UNSET:
            field_dict["source_trace_id"] = source_trace_id
        if source_span_id is not UNSET:
            field_dict["source_span_id"] = source_span_id
        if content_hash is not UNSET:
            field_dict["content_hash"] = content_hash
        if legacy_row is not UNSET:
            field_dict["legacy_row"] = legacy_row
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_version_item_read_expected_type_4_type_0 import (
            DatasetVersionItemReadExpectedType4Type0,
        )
        from ..models.dataset_version_item_read_input_type_4 import (
            DatasetVersionItemReadInputType4,
        )
        from ..models.dataset_version_item_read_metadata import (
            DatasetVersionItemReadMetadata,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _example_id = d.pop("example_id", UNSET)
        example_id: UUID | Unset
        if isinstance(_example_id, Unset):
            example_id = UNSET
        else:
            example_id = UUID(_example_id)

        def _parse_external_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        def _parse_input_(
            data: object,
        ) -> bool | DatasetVersionItemReadInputType4 | float | list[Any] | str | Unset:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_type_3 = cast(list[Any], data)

                return input_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                input_type_4 = DatasetVersionItemReadInputType4.from_dict(data)

                return input_type_4
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | DatasetVersionItemReadInputType4
                | float
                | list[Any]
                | str
                | Unset,
                data,
            )

        input_ = _parse_input_(d.pop("input", UNSET))

        def _parse_expected(
            data: object,
        ) -> (
            bool
            | DatasetVersionItemReadExpectedType4Type0
            | float
            | list[Any]
            | None
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                expected_type_3 = cast(list[Any], data)

                return expected_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                expected_type_4_type_0 = (
                    DatasetVersionItemReadExpectedType4Type0.from_dict(data)
                )

                return expected_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | DatasetVersionItemReadExpectedType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        expected = _parse_expected(d.pop("expected", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: DatasetVersionItemReadMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DatasetVersionItemReadMetadata.from_dict(_metadata)

        source_trace_id = d.pop("source_trace_id", UNSET)

        source_span_id = d.pop("source_span_id", UNSET)

        content_hash = d.pop("content_hash", UNSET)

        def _parse_legacy_row(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                legacy_row_type_0 = UUID(data)

                return legacy_row_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        legacy_row = _parse_legacy_row(d.pop("legacy_row", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        dataset_version_item_read = cls(
            id=id,
            example_id=example_id,
            external_id=external_id,
            input_=input_,
            expected=expected,
            metadata=metadata,
            source_trace_id=source_trace_id,
            source_span_id=source_span_id,
            content_hash=content_hash,
            legacy_row=legacy_row,
            created_at=created_at,
            updated_at=updated_at,
        )

        dataset_version_item_read.additional_properties = d
        return dataset_version_item_read

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
