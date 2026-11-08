from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_table_metadata_status import DatasetTableMetadataStatus


T = TypeVar("T", bound="DatasetTableMetadata")


@_attrs_define
class DatasetTableMetadata:
    """
    Attributes:
        dataset_name (str):
        experiment_id (UUID | Unset):
        experiment_name (str | Unset):
        total_rows (int | Unset):
        total_pages (int | Unset):
        page_size (int | Unset): Row limit used for this page.
        current_page_index (int | Unset): Zero-based page index returned by the server.
        has_more (bool | Unset): Whether an exact continuation page remains.
        next_page_index (int | None | Unset): Next zero-based page index, or null at exact exhaustion.
        next_cursor (None | str | Unset): Signed exact continuation cursor, or null at exhaustion.
        is_exact (bool | Unset): True only for a successful exact, revision-bound page.
        snapshot_bound (bool | Unset): Whether this page is bound to the signed MVCC revision.
        error_messages (list[str] | Unset):
        status (DatasetTableMetadataStatus | Unset):
    """

    dataset_name: str
    experiment_id: UUID | Unset = UNSET
    experiment_name: str | Unset = UNSET
    total_rows: int | Unset = UNSET
    total_pages: int | Unset = UNSET
    page_size: int | Unset = UNSET
    current_page_index: int | Unset = UNSET
    has_more: bool | Unset = UNSET
    next_page_index: int | None | Unset = UNSET
    next_cursor: None | str | Unset = UNSET
    is_exact: bool | Unset = UNSET
    snapshot_bound: bool | Unset = UNSET
    error_messages: list[str] | Unset = UNSET
    status: DatasetTableMetadataStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_name = self.dataset_name

        experiment_id: str | Unset = UNSET
        if not isinstance(self.experiment_id, Unset):
            experiment_id = str(self.experiment_id)

        experiment_name = self.experiment_name

        total_rows = self.total_rows

        total_pages = self.total_pages

        page_size = self.page_size

        current_page_index = self.current_page_index

        has_more = self.has_more

        next_page_index: int | None | Unset
        if isinstance(self.next_page_index, Unset):
            next_page_index = UNSET
        else:
            next_page_index = self.next_page_index

        next_cursor: None | str | Unset
        if isinstance(self.next_cursor, Unset):
            next_cursor = UNSET
        else:
            next_cursor = self.next_cursor

        is_exact = self.is_exact

        snapshot_bound = self.snapshot_bound

        error_messages: list[str] | Unset = UNSET
        if not isinstance(self.error_messages, Unset):
            error_messages = self.error_messages

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_name": dataset_name,
            }
        )
        if experiment_id is not UNSET:
            field_dict["experiment_id"] = experiment_id
        if experiment_name is not UNSET:
            field_dict["experiment_name"] = experiment_name
        if total_rows is not UNSET:
            field_dict["total_rows"] = total_rows
        if total_pages is not UNSET:
            field_dict["total_pages"] = total_pages
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if current_page_index is not UNSET:
            field_dict["current_page_index"] = current_page_index
        if has_more is not UNSET:
            field_dict["has_more"] = has_more
        if next_page_index is not UNSET:
            field_dict["next_page_index"] = next_page_index
        if next_cursor is not UNSET:
            field_dict["next_cursor"] = next_cursor
        if is_exact is not UNSET:
            field_dict["is_exact"] = is_exact
        if snapshot_bound is not UNSET:
            field_dict["snapshot_bound"] = snapshot_bound
        if error_messages is not UNSET:
            field_dict["error_messages"] = error_messages
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_table_metadata_status import DatasetTableMetadataStatus

        d = dict(src_dict)
        dataset_name = d.pop("dataset_name")

        _experiment_id = d.pop("experiment_id", UNSET)
        experiment_id: UUID | Unset
        if isinstance(_experiment_id, Unset):
            experiment_id = UNSET
        else:
            experiment_id = UUID(_experiment_id)

        experiment_name = d.pop("experiment_name", UNSET)

        total_rows = d.pop("total_rows", UNSET)

        total_pages = d.pop("total_pages", UNSET)

        page_size = d.pop("page_size", UNSET)

        current_page_index = d.pop("current_page_index", UNSET)

        has_more = d.pop("has_more", UNSET)

        def _parse_next_page_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        next_page_index = _parse_next_page_index(d.pop("next_page_index", UNSET))

        def _parse_next_cursor(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_cursor = _parse_next_cursor(d.pop("next_cursor", UNSET))

        is_exact = d.pop("is_exact", UNSET)

        snapshot_bound = d.pop("snapshot_bound", UNSET)

        error_messages = cast(list[str], d.pop("error_messages", UNSET))

        _status = d.pop("status", UNSET)
        status: DatasetTableMetadataStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DatasetTableMetadataStatus.from_dict(_status)

        dataset_table_metadata = cls(
            dataset_name=dataset_name,
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            total_rows=total_rows,
            total_pages=total_pages,
            page_size=page_size,
            current_page_index=current_page_index,
            has_more=has_more,
            next_page_index=next_page_index,
            next_cursor=next_cursor,
            is_exact=is_exact,
            snapshot_bound=snapshot_bound,
            error_messages=error_messages,
            status=status,
        )

        dataset_table_metadata.additional_properties = d
        return dataset_table_metadata

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
