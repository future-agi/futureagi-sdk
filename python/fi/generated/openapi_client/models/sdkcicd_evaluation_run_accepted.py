from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SDKCICDEvaluationRunAccepted")


@_attrs_define
class SDKCICDEvaluationRunAccepted:
    """
    Attributes:
        message (str):
        project_name (str):
        version (str):
        evaluation_run_id (UUID):
    """

    message: str
    project_name: str
    version: str
    evaluation_run_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        project_name = self.project_name

        version = self.version

        evaluation_run_id = str(self.evaluation_run_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "project_name": project_name,
                "version": version,
                "evaluation_run_id": evaluation_run_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        project_name = d.pop("project_name")

        version = d.pop("version")

        evaluation_run_id = UUID(d.pop("evaluation_run_id"))

        sdkcicd_evaluation_run_accepted = cls(
            message=message,
            project_name=project_name,
            version=version,
            evaluation_run_id=evaluation_run_id,
        )

        sdkcicd_evaluation_run_accepted.additional_properties = d
        return sdkcicd_evaluation_run_accepted

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
