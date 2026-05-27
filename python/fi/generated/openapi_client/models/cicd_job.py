from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cicd_evaluation_item import CICDEvaluationItem


T = TypeVar("T", bound="CICDJob")


@_attrs_define
class CICDJob:
    """
    Attributes:
        project_name (str):
        version (str):
        eval_data (list[CICDEvaluationItem]):
    """

    project_name: str
    version: str
    eval_data: list[CICDEvaluationItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_name = self.project_name

        version = self.version

        eval_data = []
        for eval_data_item_data in self.eval_data:
            eval_data_item = eval_data_item_data.to_dict()
            eval_data.append(eval_data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_name": project_name,
                "version": version,
                "eval_data": eval_data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cicd_evaluation_item import CICDEvaluationItem

        d = dict(src_dict)
        project_name = d.pop("project_name")

        version = d.pop("version")

        eval_data = []
        _eval_data = d.pop("eval_data")
        for eval_data_item_data in _eval_data:
            eval_data_item = CICDEvaluationItem.from_dict(eval_data_item_data)

            eval_data.append(eval_data_item)

        cicd_job = cls(
            project_name=project_name,
            version=version,
            eval_data=eval_data,
        )

        cicd_job.additional_properties = d
        return cicd_job

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
