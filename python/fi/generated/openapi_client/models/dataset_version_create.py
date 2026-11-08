from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_version_create_metadata import DatasetVersionCreateMetadata
    from ..models.dataset_version_item_create import DatasetVersionItemCreate


T = TypeVar("T", bound="DatasetVersionCreate")


@_attrs_define
class DatasetVersionCreate:
    """
    Attributes:
        items (list[DatasetVersionItemCreate]):
        parent_version_id (None | Unset | UUID):
        description (str | Unset):
        metadata (DatasetVersionCreateMetadata | Unset):
        source_revision (str | Unset):
    """

    items: list[DatasetVersionItemCreate]
    parent_version_id: None | Unset | UUID = UNSET
    description: str | Unset = UNSET
    metadata: DatasetVersionCreateMetadata | Unset = UNSET
    source_revision: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        parent_version_id: None | str | Unset
        if isinstance(self.parent_version_id, Unset):
            parent_version_id = UNSET
        elif isinstance(self.parent_version_id, UUID):
            parent_version_id = str(self.parent_version_id)
        else:
            parent_version_id = self.parent_version_id

        description = self.description

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        source_revision = self.source_revision

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "items": items,
            }
        )
        if parent_version_id is not UNSET:
            field_dict["parent_version_id"] = parent_version_id
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if source_revision is not UNSET:
            field_dict["source_revision"] = source_revision

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_version_create_metadata import (
            DatasetVersionCreateMetadata,
        )
        from ..models.dataset_version_item_create import DatasetVersionItemCreate

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = DatasetVersionItemCreate.from_dict(items_item_data)

            items.append(items_item)

        def _parse_parent_version_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                parent_version_id_type_0 = UUID(data)

                return parent_version_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        parent_version_id = _parse_parent_version_id(d.pop("parent_version_id", UNSET))

        description = d.pop("description", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: DatasetVersionCreateMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DatasetVersionCreateMetadata.from_dict(_metadata)

        source_revision = d.pop("source_revision", UNSET)

        dataset_version_create = cls(
            items=items,
            parent_version_id=parent_version_id,
            description=description,
            metadata=metadata,
            source_revision=source_revision,
        )

        return dataset_version_create
