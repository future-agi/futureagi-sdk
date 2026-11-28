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
    from ..models.dataset_version_read_metadata import DatasetVersionReadMetadata


T = TypeVar("T", bound="DatasetVersionRead")


@_attrs_define
class DatasetVersionRead:
    """
    Attributes:
        id (UUID | Unset):
        dataset (UUID | Unset):
        parent_version (None | Unset | UUID):
        created_by (None | Unset | UUID):
        organization (None | Unset | UUID):
        workspace (None | Unset | UUID):
        content_hash (str | Unset):
        description (str | Unset):
        metadata (DatasetVersionReadMetadata | Unset):
        source_revision (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        item_count (int | Unset):
    """

    id: UUID | Unset = UNSET
    dataset: UUID | Unset = UNSET
    parent_version: None | Unset | UUID = UNSET
    created_by: None | Unset | UUID = UNSET
    organization: None | Unset | UUID = UNSET
    workspace: None | Unset | UUID = UNSET
    content_hash: str | Unset = UNSET
    description: str | Unset = UNSET
    metadata: DatasetVersionReadMetadata | Unset = UNSET
    source_revision: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    item_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        dataset: str | Unset = UNSET
        if not isinstance(self.dataset, Unset):
            dataset = str(self.dataset)

        parent_version: None | str | Unset
        if isinstance(self.parent_version, Unset):
            parent_version = UNSET
        elif isinstance(self.parent_version, UUID):
            parent_version = str(self.parent_version)
        else:
            parent_version = self.parent_version

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        elif isinstance(self.created_by, UUID):
            created_by = str(self.created_by)
        else:
            created_by = self.created_by

        organization: None | str | Unset
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, UUID):
            organization = str(self.organization)
        else:
            organization = self.organization

        workspace: None | str | Unset
        if isinstance(self.workspace, Unset):
            workspace = UNSET
        elif isinstance(self.workspace, UUID):
            workspace = str(self.workspace)
        else:
            workspace = self.workspace

        content_hash = self.content_hash

        description = self.description

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        source_revision = self.source_revision

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        item_count = self.item_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if parent_version is not UNSET:
            field_dict["parent_version"] = parent_version
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if organization is not UNSET:
            field_dict["organization"] = organization
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if content_hash is not UNSET:
            field_dict["content_hash"] = content_hash
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if source_revision is not UNSET:
            field_dict["source_revision"] = source_revision
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if item_count is not UNSET:
            field_dict["item_count"] = item_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_version_read_metadata import DatasetVersionReadMetadata

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _dataset = d.pop("dataset", UNSET)
        dataset: UUID | Unset
        if isinstance(_dataset, Unset):
            dataset = UNSET
        else:
            dataset = UUID(_dataset)

        def _parse_parent_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                parent_version_type_0 = UUID(data)

                return parent_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        parent_version = _parse_parent_version(d.pop("parent_version", UNSET))

        def _parse_created_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_by_type_0 = UUID(data)

                return created_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        def _parse_organization(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                organization_type_0 = UUID(data)

                return organization_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        organization = _parse_organization(d.pop("organization", UNSET))

        def _parse_workspace(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                workspace_type_0 = UUID(data)

                return workspace_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        workspace = _parse_workspace(d.pop("workspace", UNSET))

        content_hash = d.pop("content_hash", UNSET)

        description = d.pop("description", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: DatasetVersionReadMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DatasetVersionReadMetadata.from_dict(_metadata)

        source_revision = d.pop("source_revision", UNSET)

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

        item_count = d.pop("item_count", UNSET)

        dataset_version_read = cls(
            id=id,
            dataset=dataset,
            parent_version=parent_version,
            created_by=created_by,
            organization=organization,
            workspace=workspace,
            content_hash=content_hash,
            description=description,
            metadata=metadata,
            source_revision=source_revision,
            created_at=created_at,
            updated_at=updated_at,
            item_count=item_count,
        )

        dataset_version_read.additional_properties = d
        return dataset_version_read

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
