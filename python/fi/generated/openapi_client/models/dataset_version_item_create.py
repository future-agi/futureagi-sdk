from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_version_item_create_expected_type_4_type_0 import (
        DatasetVersionItemCreateExpectedType4Type0,
    )
    from ..models.dataset_version_item_create_input_type_4 import (
        DatasetVersionItemCreateInputType4,
    )
    from ..models.dataset_version_item_create_metadata import (
        DatasetVersionItemCreateMetadata,
    )


T = TypeVar("T", bound="DatasetVersionItemCreate")


@_attrs_define
class DatasetVersionItemCreate:
    """
    Attributes:
        input_ (bool | DatasetVersionItemCreateInputType4 | float | list[Any] | str): Any non-null JSON value; nested
            nulls are allowed.
        expected (bool | DatasetVersionItemCreateExpectedType4Type0 | float | list[Any] | None | str | Unset): Any valid
            JSON value.
        metadata (DatasetVersionItemCreateMetadata | Unset):
        example_id (None | Unset | UUID):
        external_id (None | str | Unset):
        source_trace_id (None | str | Unset):
        source_span_id (None | str | Unset):
        legacy_row_id (None | Unset | UUID):
    """

    input_: bool | DatasetVersionItemCreateInputType4 | float | list[Any] | str
    expected: (
        bool
        | DatasetVersionItemCreateExpectedType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    metadata: DatasetVersionItemCreateMetadata | Unset = UNSET
    example_id: None | Unset | UUID = UNSET
    external_id: None | str | Unset = UNSET
    source_trace_id: None | str | Unset = UNSET
    source_span_id: None | str | Unset = UNSET
    legacy_row_id: None | Unset | UUID = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.dataset_version_item_create_expected_type_4_type_0 import (
            DatasetVersionItemCreateExpectedType4Type0,
        )
        from ..models.dataset_version_item_create_input_type_4 import (
            DatasetVersionItemCreateInputType4,
        )

        input_: bool | dict[str, Any] | float | list[Any] | str
        if isinstance(self.input_, list):
            input_ = self.input_

        elif isinstance(self.input_, DatasetVersionItemCreateInputType4):
            input_ = self.input_.to_dict()
        else:
            input_ = self.input_

        expected: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.expected, Unset):
            expected = UNSET
        elif isinstance(self.expected, list):
            expected = self.expected

        elif isinstance(self.expected, DatasetVersionItemCreateExpectedType4Type0):
            expected = self.expected.to_dict()
        else:
            expected = self.expected

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        example_id: None | str | Unset
        if isinstance(self.example_id, Unset):
            example_id = UNSET
        elif isinstance(self.example_id, UUID):
            example_id = str(self.example_id)
        else:
            example_id = self.example_id

        external_id: None | str | Unset
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        source_trace_id: None | str | Unset
        if isinstance(self.source_trace_id, Unset):
            source_trace_id = UNSET
        else:
            source_trace_id = self.source_trace_id

        source_span_id: None | str | Unset
        if isinstance(self.source_span_id, Unset):
            source_span_id = UNSET
        else:
            source_span_id = self.source_span_id

        legacy_row_id: None | str | Unset
        if isinstance(self.legacy_row_id, Unset):
            legacy_row_id = UNSET
        elif isinstance(self.legacy_row_id, UUID):
            legacy_row_id = str(self.legacy_row_id)
        else:
            legacy_row_id = self.legacy_row_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "input": input_,
            }
        )
        if expected is not UNSET:
            field_dict["expected"] = expected
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if example_id is not UNSET:
            field_dict["example_id"] = example_id
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if source_trace_id is not UNSET:
            field_dict["source_trace_id"] = source_trace_id
        if source_span_id is not UNSET:
            field_dict["source_span_id"] = source_span_id
        if legacy_row_id is not UNSET:
            field_dict["legacy_row_id"] = legacy_row_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_version_item_create_expected_type_4_type_0 import (
            DatasetVersionItemCreateExpectedType4Type0,
        )
        from ..models.dataset_version_item_create_input_type_4 import (
            DatasetVersionItemCreateInputType4,
        )
        from ..models.dataset_version_item_create_metadata import (
            DatasetVersionItemCreateMetadata,
        )

        d = dict(src_dict)

        def _parse_input_(
            data: object,
        ) -> bool | DatasetVersionItemCreateInputType4 | float | list[Any] | str:
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
                input_type_4 = DatasetVersionItemCreateInputType4.from_dict(data)

                return input_type_4
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool | DatasetVersionItemCreateInputType4 | float | list[Any] | str,
                data,
            )

        input_ = _parse_input_(d.pop("input"))

        def _parse_expected(
            data: object,
        ) -> (
            bool
            | DatasetVersionItemCreateExpectedType4Type0
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
                    DatasetVersionItemCreateExpectedType4Type0.from_dict(data)
                )

                return expected_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | DatasetVersionItemCreateExpectedType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        expected = _parse_expected(d.pop("expected", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: DatasetVersionItemCreateMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DatasetVersionItemCreateMetadata.from_dict(_metadata)

        def _parse_example_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                example_id_type_0 = UUID(data)

                return example_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        example_id = _parse_example_id(d.pop("example_id", UNSET))

        def _parse_external_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        def _parse_source_trace_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_trace_id = _parse_source_trace_id(d.pop("source_trace_id", UNSET))

        def _parse_source_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_span_id = _parse_source_span_id(d.pop("source_span_id", UNSET))

        def _parse_legacy_row_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                legacy_row_id_type_0 = UUID(data)

                return legacy_row_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        legacy_row_id = _parse_legacy_row_id(d.pop("legacy_row_id", UNSET))

        dataset_version_item_create = cls(
            input_=input_,
            expected=expected,
            metadata=metadata,
            example_id=example_id,
            external_id=external_id,
            source_trace_id=source_trace_id,
            source_span_id=source_span_id,
            legacy_row_id=legacy_row_id,
        )

        return dataset_version_item_create
