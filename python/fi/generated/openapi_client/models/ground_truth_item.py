from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ground_truth_item_variable_mapping import (
        GroundTruthItemVariableMapping,
    )
    from ..models.ground_truth_role_mapping import GroundTruthRoleMapping


T = TypeVar("T", bound="GroundTruthItem")


@_attrs_define
class GroundTruthItem:
    """
    Attributes:
        id (UUID):
        name (str):
        columns (list[str]):
        row_count (int):
        description (str | Unset):
        file_name (str | Unset):
        variable_mapping (GroundTruthItemVariableMapping | Unset): Map of template variable name to GT column name
            (string) or list of column names.
        role_mapping (GroundTruthRoleMapping | Unset):
        embedding_status (str | Unset):
        embedded_row_count (int | Unset):
        storage_type (str | Unset):
        created_at (str | Unset):
        embeddings_stale (bool | Unset):  Default: False.
        is_active (bool | Unset):  Default: False.
        enabled (bool | Unset):  Default: True.
        max_examples (int | Unset):  Default: 3.
        similarity_threshold (float | Unset):  Default: 0.7.
    """

    id: UUID
    name: str
    columns: list[str]
    row_count: int
    description: str | Unset = UNSET
    file_name: str | Unset = UNSET
    variable_mapping: GroundTruthItemVariableMapping | Unset = UNSET
    role_mapping: GroundTruthRoleMapping | Unset = UNSET
    embedding_status: str | Unset = UNSET
    embedded_row_count: int | Unset = UNSET
    storage_type: str | Unset = UNSET
    created_at: str | Unset = UNSET
    embeddings_stale: bool | Unset = False
    is_active: bool | Unset = False
    enabled: bool | Unset = True
    max_examples: int | Unset = 3
    similarity_threshold: float | Unset = 0.7
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        columns = self.columns

        row_count = self.row_count

        description = self.description

        file_name = self.file_name

        variable_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variable_mapping, Unset):
            variable_mapping = self.variable_mapping.to_dict()

        role_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.role_mapping, Unset):
            role_mapping = self.role_mapping.to_dict()

        embedding_status = self.embedding_status

        embedded_row_count = self.embedded_row_count

        storage_type = self.storage_type

        created_at = self.created_at

        embeddings_stale = self.embeddings_stale

        is_active = self.is_active

        enabled = self.enabled

        max_examples = self.max_examples

        similarity_threshold = self.similarity_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "columns": columns,
                "row_count": row_count,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if file_name is not UNSET:
            field_dict["file_name"] = file_name
        if variable_mapping is not UNSET:
            field_dict["variable_mapping"] = variable_mapping
        if role_mapping is not UNSET:
            field_dict["role_mapping"] = role_mapping
        if embedding_status is not UNSET:
            field_dict["embedding_status"] = embedding_status
        if embedded_row_count is not UNSET:
            field_dict["embedded_row_count"] = embedded_row_count
        if storage_type is not UNSET:
            field_dict["storage_type"] = storage_type
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if embeddings_stale is not UNSET:
            field_dict["embeddings_stale"] = embeddings_stale
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if max_examples is not UNSET:
            field_dict["max_examples"] = max_examples
        if similarity_threshold is not UNSET:
            field_dict["similarity_threshold"] = similarity_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ground_truth_item_variable_mapping import (
            GroundTruthItemVariableMapping,
        )
        from ..models.ground_truth_role_mapping import GroundTruthRoleMapping

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        columns = cast(list[str], d.pop("columns"))

        row_count = d.pop("row_count")

        description = d.pop("description", UNSET)

        file_name = d.pop("file_name", UNSET)

        _variable_mapping = d.pop("variable_mapping", UNSET)
        variable_mapping: GroundTruthItemVariableMapping | Unset
        if isinstance(_variable_mapping, Unset):
            variable_mapping = UNSET
        else:
            variable_mapping = GroundTruthItemVariableMapping.from_dict(
                _variable_mapping
            )

        _role_mapping = d.pop("role_mapping", UNSET)
        role_mapping: GroundTruthRoleMapping | Unset
        if isinstance(_role_mapping, Unset):
            role_mapping = UNSET
        else:
            role_mapping = GroundTruthRoleMapping.from_dict(_role_mapping)

        embedding_status = d.pop("embedding_status", UNSET)

        embedded_row_count = d.pop("embedded_row_count", UNSET)

        storage_type = d.pop("storage_type", UNSET)

        created_at = d.pop("created_at", UNSET)

        embeddings_stale = d.pop("embeddings_stale", UNSET)

        is_active = d.pop("is_active", UNSET)

        enabled = d.pop("enabled", UNSET)

        max_examples = d.pop("max_examples", UNSET)

        similarity_threshold = d.pop("similarity_threshold", UNSET)

        ground_truth_item = cls(
            id=id,
            name=name,
            columns=columns,
            row_count=row_count,
            description=description,
            file_name=file_name,
            variable_mapping=variable_mapping,
            role_mapping=role_mapping,
            embedding_status=embedding_status,
            embedded_row_count=embedded_row_count,
            storage_type=storage_type,
            created_at=created_at,
            embeddings_stale=embeddings_stale,
            is_active=is_active,
            enabled=enabled,
            max_examples=max_examples,
            similarity_threshold=similarity_threshold,
        )

        ground_truth_item.additional_properties = d
        return ground_truth_item

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
