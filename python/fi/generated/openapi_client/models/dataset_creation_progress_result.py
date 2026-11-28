from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetCreationProgressResult")


@_attrs_define
class DatasetCreationProgressResult:
    """
    Attributes:
        dataset_id (UUID):
        dataset_name (str):
        processing_status (str):
        is_processing (bool):
        is_completed (bool):
        is_failed (bool):
        original_filename (None | str | Unset):
        estimated_rows (int | None | Unset):
        estimated_columns (int | None | Unset):
        queued_at (None | str | Unset):
        started_at (None | str | Unset):
        completed_at (None | str | Unset):
        failed_at (None | str | Unset):
        error_message (None | str | Unset):
    """

    dataset_id: UUID
    dataset_name: str
    processing_status: str
    is_processing: bool
    is_completed: bool
    is_failed: bool
    original_filename: None | str | Unset = UNSET
    estimated_rows: int | None | Unset = UNSET
    estimated_columns: int | None | Unset = UNSET
    queued_at: None | str | Unset = UNSET
    started_at: None | str | Unset = UNSET
    completed_at: None | str | Unset = UNSET
    failed_at: None | str | Unset = UNSET
    error_message: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        processing_status = self.processing_status

        is_processing = self.is_processing

        is_completed = self.is_completed

        is_failed = self.is_failed

        original_filename: None | str | Unset
        if isinstance(self.original_filename, Unset):
            original_filename = UNSET
        else:
            original_filename = self.original_filename

        estimated_rows: int | None | Unset
        if isinstance(self.estimated_rows, Unset):
            estimated_rows = UNSET
        else:
            estimated_rows = self.estimated_rows

        estimated_columns: int | None | Unset
        if isinstance(self.estimated_columns, Unset):
            estimated_columns = UNSET
        else:
            estimated_columns = self.estimated_columns

        queued_at: None | str | Unset
        if isinstance(self.queued_at, Unset):
            queued_at = UNSET
        else:
            queued_at = self.queued_at

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        else:
            started_at = self.started_at

        completed_at: None | str | Unset
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        else:
            completed_at = self.completed_at

        failed_at: None | str | Unset
        if isinstance(self.failed_at, Unset):
            failed_at = UNSET
        else:
            failed_at = self.failed_at

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "processing_status": processing_status,
                "is_processing": is_processing,
                "is_completed": is_completed,
                "is_failed": is_failed,
            }
        )
        if original_filename is not UNSET:
            field_dict["original_filename"] = original_filename
        if estimated_rows is not UNSET:
            field_dict["estimated_rows"] = estimated_rows
        if estimated_columns is not UNSET:
            field_dict["estimated_columns"] = estimated_columns
        if queued_at is not UNSET:
            field_dict["queued_at"] = queued_at
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if failed_at is not UNSET:
            field_dict["failed_at"] = failed_at
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        dataset_name = d.pop("dataset_name")

        processing_status = d.pop("processing_status")

        is_processing = d.pop("is_processing")

        is_completed = d.pop("is_completed")

        is_failed = d.pop("is_failed")

        def _parse_original_filename(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        original_filename = _parse_original_filename(d.pop("original_filename", UNSET))

        def _parse_estimated_rows(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        estimated_rows = _parse_estimated_rows(d.pop("estimated_rows", UNSET))

        def _parse_estimated_columns(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        estimated_columns = _parse_estimated_columns(d.pop("estimated_columns", UNSET))

        def _parse_queued_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        queued_at = _parse_queued_at(d.pop("queued_at", UNSET))

        def _parse_started_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_completed_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

        def _parse_failed_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        failed_at = _parse_failed_at(d.pop("failed_at", UNSET))

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        dataset_creation_progress_result = cls(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            processing_status=processing_status,
            is_processing=is_processing,
            is_completed=is_completed,
            is_failed=is_failed,
            original_filename=original_filename,
            estimated_rows=estimated_rows,
            estimated_columns=estimated_columns,
            queued_at=queued_at,
            started_at=started_at,
            completed_at=completed_at,
            failed_at=failed_at,
            error_message=error_message,
        )

        dataset_creation_progress_result.additional_properties = d
        return dataset_creation_progress_result

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
