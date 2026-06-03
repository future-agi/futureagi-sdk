from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.queue_item_source_type import QueueItemSourceType
from ..models.queue_item_status import QueueItemStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_item_metadata import QueueItemMetadata


T = TypeVar("T", bound="QueueItem")


@_attrs_define
class QueueItem:
    """
    Attributes:
        source_type (QueueItemSourceType):
        id (UUID | Unset):
        queue (UUID | Unset):
        source_id (str | Unset):
        status (QueueItemStatus | Unset):
        workflow_status (str | Unset):
        workflow_status_label (str | Unset):
        priority (int | Unset):
        order (int | Unset):
        metadata (QueueItemMetadata | Unset):
        assigned_to (None | Unset | UUID):
        assigned_to_name (str | Unset):
        assigned_users (str | Unset):
        reserved_by (None | Unset | UUID):
        reserved_by_name (str | Unset):
        reservation_expires_at (datetime.datetime | None | Unset):
        review_status (None | str | Unset):
        reviewed_by (None | Unset | UUID):
        reviewed_by_name (str | Unset):
        reviewed_at (datetime.datetime | None | Unset):
        review_notes (None | str | Unset):
        source_preview (str | Unset):
        created_at (datetime.datetime | Unset):
    """

    source_type: QueueItemSourceType
    id: UUID | Unset = UNSET
    queue: UUID | Unset = UNSET
    source_id: str | Unset = UNSET
    status: QueueItemStatus | Unset = UNSET
    workflow_status: str | Unset = UNSET
    workflow_status_label: str | Unset = UNSET
    priority: int | Unset = UNSET
    order: int | Unset = UNSET
    metadata: QueueItemMetadata | Unset = UNSET
    assigned_to: None | Unset | UUID = UNSET
    assigned_to_name: str | Unset = UNSET
    assigned_users: str | Unset = UNSET
    reserved_by: None | Unset | UUID = UNSET
    reserved_by_name: str | Unset = UNSET
    reservation_expires_at: datetime.datetime | None | Unset = UNSET
    review_status: None | str | Unset = UNSET
    reviewed_by: None | Unset | UUID = UNSET
    reviewed_by_name: str | Unset = UNSET
    reviewed_at: datetime.datetime | None | Unset = UNSET
    review_notes: None | str | Unset = UNSET
    source_preview: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        queue: str | Unset = UNSET
        if not isinstance(self.queue, Unset):
            queue = str(self.queue)

        source_id = self.source_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        workflow_status = self.workflow_status

        workflow_status_label = self.workflow_status_label

        priority = self.priority

        order = self.order

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        assigned_to: None | str | Unset
        if isinstance(self.assigned_to, Unset):
            assigned_to = UNSET
        elif isinstance(self.assigned_to, UUID):
            assigned_to = str(self.assigned_to)
        else:
            assigned_to = self.assigned_to

        assigned_to_name = self.assigned_to_name

        assigned_users = self.assigned_users

        reserved_by: None | str | Unset
        if isinstance(self.reserved_by, Unset):
            reserved_by = UNSET
        elif isinstance(self.reserved_by, UUID):
            reserved_by = str(self.reserved_by)
        else:
            reserved_by = self.reserved_by

        reserved_by_name = self.reserved_by_name

        reservation_expires_at: None | str | Unset
        if isinstance(self.reservation_expires_at, Unset):
            reservation_expires_at = UNSET
        elif isinstance(self.reservation_expires_at, datetime.datetime):
            reservation_expires_at = self.reservation_expires_at.isoformat()
        else:
            reservation_expires_at = self.reservation_expires_at

        review_status: None | str | Unset
        if isinstance(self.review_status, Unset):
            review_status = UNSET
        else:
            review_status = self.review_status

        reviewed_by: None | str | Unset
        if isinstance(self.reviewed_by, Unset):
            reviewed_by = UNSET
        elif isinstance(self.reviewed_by, UUID):
            reviewed_by = str(self.reviewed_by)
        else:
            reviewed_by = self.reviewed_by

        reviewed_by_name = self.reviewed_by_name

        reviewed_at: None | str | Unset
        if isinstance(self.reviewed_at, Unset):
            reviewed_at = UNSET
        elif isinstance(self.reviewed_at, datetime.datetime):
            reviewed_at = self.reviewed_at.isoformat()
        else:
            reviewed_at = self.reviewed_at

        review_notes: None | str | Unset
        if isinstance(self.review_notes, Unset):
            review_notes = UNSET
        else:
            review_notes = self.review_notes

        source_preview = self.source_preview

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_type": source_type,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if queue is not UNSET:
            field_dict["queue"] = queue
        if source_id is not UNSET:
            field_dict["source_id"] = source_id
        if status is not UNSET:
            field_dict["status"] = status
        if workflow_status is not UNSET:
            field_dict["workflow_status"] = workflow_status
        if workflow_status_label is not UNSET:
            field_dict["workflow_status_label"] = workflow_status_label
        if priority is not UNSET:
            field_dict["priority"] = priority
        if order is not UNSET:
            field_dict["order"] = order
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if assigned_to is not UNSET:
            field_dict["assigned_to"] = assigned_to
        if assigned_to_name is not UNSET:
            field_dict["assigned_to_name"] = assigned_to_name
        if assigned_users is not UNSET:
            field_dict["assigned_users"] = assigned_users
        if reserved_by is not UNSET:
            field_dict["reserved_by"] = reserved_by
        if reserved_by_name is not UNSET:
            field_dict["reserved_by_name"] = reserved_by_name
        if reservation_expires_at is not UNSET:
            field_dict["reservation_expires_at"] = reservation_expires_at
        if review_status is not UNSET:
            field_dict["review_status"] = review_status
        if reviewed_by is not UNSET:
            field_dict["reviewed_by"] = reviewed_by
        if reviewed_by_name is not UNSET:
            field_dict["reviewed_by_name"] = reviewed_by_name
        if reviewed_at is not UNSET:
            field_dict["reviewed_at"] = reviewed_at
        if review_notes is not UNSET:
            field_dict["review_notes"] = review_notes
        if source_preview is not UNSET:
            field_dict["source_preview"] = source_preview
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_item_metadata import QueueItemMetadata

        d = dict(src_dict)
        source_type = QueueItemSourceType(d.pop("source_type"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _queue = d.pop("queue", UNSET)
        queue: UUID | Unset
        if isinstance(_queue, Unset):
            queue = UNSET
        else:
            queue = UUID(_queue)

        source_id = d.pop("source_id", UNSET)

        _status = d.pop("status", UNSET)
        status: QueueItemStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = QueueItemStatus(_status)

        workflow_status = d.pop("workflow_status", UNSET)

        workflow_status_label = d.pop("workflow_status_label", UNSET)

        priority = d.pop("priority", UNSET)

        order = d.pop("order", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: QueueItemMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = QueueItemMetadata.from_dict(_metadata)

        def _parse_assigned_to(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                assigned_to_type_0 = UUID(data)

                return assigned_to_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        assigned_to = _parse_assigned_to(d.pop("assigned_to", UNSET))

        assigned_to_name = d.pop("assigned_to_name", UNSET)

        assigned_users = d.pop("assigned_users", UNSET)

        def _parse_reserved_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                reserved_by_type_0 = UUID(data)

                return reserved_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        reserved_by = _parse_reserved_by(d.pop("reserved_by", UNSET))

        reserved_by_name = d.pop("reserved_by_name", UNSET)

        def _parse_reservation_expires_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                reservation_expires_at_type_0 = isoparse(data)

                return reservation_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        reservation_expires_at = _parse_reservation_expires_at(
            d.pop("reservation_expires_at", UNSET)
        )

        def _parse_review_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        review_status = _parse_review_status(d.pop("review_status", UNSET))

        def _parse_reviewed_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                reviewed_by_type_0 = UUID(data)

                return reviewed_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        reviewed_by = _parse_reviewed_by(d.pop("reviewed_by", UNSET))

        reviewed_by_name = d.pop("reviewed_by_name", UNSET)

        def _parse_reviewed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                reviewed_at_type_0 = isoparse(data)

                return reviewed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        reviewed_at = _parse_reviewed_at(d.pop("reviewed_at", UNSET))

        def _parse_review_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        review_notes = _parse_review_notes(d.pop("review_notes", UNSET))

        source_preview = d.pop("source_preview", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        queue_item = cls(
            source_type=source_type,
            id=id,
            queue=queue,
            source_id=source_id,
            status=status,
            workflow_status=workflow_status,
            workflow_status_label=workflow_status_label,
            priority=priority,
            order=order,
            metadata=metadata,
            assigned_to=assigned_to,
            assigned_to_name=assigned_to_name,
            assigned_users=assigned_users,
            reserved_by=reserved_by,
            reserved_by_name=reserved_by_name,
            reservation_expires_at=reservation_expires_at,
            review_status=review_status,
            reviewed_by=reviewed_by,
            reviewed_by_name=reviewed_by_name,
            reviewed_at=reviewed_at,
            review_notes=review_notes,
            source_preview=source_preview,
            created_at=created_at,
        )

        queue_item.additional_properties = d
        return queue_item

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
