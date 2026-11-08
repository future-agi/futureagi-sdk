from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ground_truth_upload_request_data_item import (
        GroundTruthUploadRequestDataItem,
    )
    from ..models.ground_truth_upload_request_role_mapping import (
        GroundTruthUploadRequestRoleMapping,
    )
    from ..models.ground_truth_upload_request_variable_mapping import (
        GroundTruthUploadRequestVariableMapping,
    )


T = TypeVar("T", bound="GroundTruthUploadRequest")


@_attrs_define
class GroundTruthUploadRequest:
    """
    Attributes:
        file (str | Unset):
        name (str | Unset):
        description (str | Unset):  Default: ''.
        file_name (str | Unset):  Default: ''.
        columns (list[str] | Unset):
        data (list[GroundTruthUploadRequestDataItem] | Unset):
        variable_mapping (GroundTruthUploadRequestVariableMapping | Unset):
        role_mapping (GroundTruthUploadRequestRoleMapping | Unset):
    """

    file: str | Unset = UNSET
    name: str | Unset = UNSET
    description: str | Unset = ""
    file_name: str | Unset = ""
    columns: list[str] | Unset = UNSET
    data: list[GroundTruthUploadRequestDataItem] | Unset = UNSET
    variable_mapping: GroundTruthUploadRequestVariableMapping | Unset = UNSET
    role_mapping: GroundTruthUploadRequestRoleMapping | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        name = self.name

        description = self.description

        file_name = self.file_name

        columns: list[str] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = self.columns

        data: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        variable_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variable_mapping, Unset):
            variable_mapping = self.variable_mapping.to_dict()

        role_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.role_mapping, Unset):
            role_mapping = self.role_mapping.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file is not UNSET:
            field_dict["file"] = file
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if file_name is not UNSET:
            field_dict["file_name"] = file_name
        if columns is not UNSET:
            field_dict["columns"] = columns
        if data is not UNSET:
            field_dict["data"] = data
        if variable_mapping is not UNSET:
            field_dict["variable_mapping"] = variable_mapping
        if role_mapping is not UNSET:
            field_dict["role_mapping"] = role_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ground_truth_upload_request_data_item import (
            GroundTruthUploadRequestDataItem,
        )
        from ..models.ground_truth_upload_request_role_mapping import (
            GroundTruthUploadRequestRoleMapping,
        )
        from ..models.ground_truth_upload_request_variable_mapping import (
            GroundTruthUploadRequestVariableMapping,
        )

        d = dict(src_dict)
        file = d.pop("file", UNSET)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        file_name = d.pop("file_name", UNSET)

        columns = cast(list[str], d.pop("columns", UNSET))

        _data = d.pop("data", UNSET)
        data: list[GroundTruthUploadRequestDataItem] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = GroundTruthUploadRequestDataItem.from_dict(data_item_data)

                data.append(data_item)

        _variable_mapping = d.pop("variable_mapping", UNSET)
        variable_mapping: GroundTruthUploadRequestVariableMapping | Unset
        if isinstance(_variable_mapping, Unset):
            variable_mapping = UNSET
        else:
            variable_mapping = GroundTruthUploadRequestVariableMapping.from_dict(
                _variable_mapping
            )

        _role_mapping = d.pop("role_mapping", UNSET)
        role_mapping: GroundTruthUploadRequestRoleMapping | Unset
        if isinstance(_role_mapping, Unset):
            role_mapping = UNSET
        else:
            role_mapping = GroundTruthUploadRequestRoleMapping.from_dict(_role_mapping)

        ground_truth_upload_request = cls(
            file=file,
            name=name,
            description=description,
            file_name=file_name,
            columns=columns,
            data=data,
            variable_mapping=variable_mapping,
            role_mapping=role_mapping,
        )

        ground_truth_upload_request.additional_properties = d
        return ground_truth_upload_request

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
