from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.experiment_stop_workflows_cancelled import (
        ExperimentStopWorkflowsCancelled,
    )


T = TypeVar("T", bound="ExperimentStopResult")


@_attrs_define
class ExperimentStopResult:
    """
    Attributes:
        message (str):
        experiment_id (UUID):
        workflows_cancelled (ExperimentStopWorkflowsCancelled):
    """

    message: str
    experiment_id: UUID
    workflows_cancelled: ExperimentStopWorkflowsCancelled
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        experiment_id = str(self.experiment_id)

        workflows_cancelled = self.workflows_cancelled.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "experiment_id": experiment_id,
                "workflows_cancelled": workflows_cancelled,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_stop_workflows_cancelled import (
            ExperimentStopWorkflowsCancelled,
        )

        d = dict(src_dict)
        message = d.pop("message")

        experiment_id = UUID(d.pop("experiment_id"))

        workflows_cancelled = ExperimentStopWorkflowsCancelled.from_dict(
            d.pop("workflows_cancelled")
        )

        experiment_stop_result = cls(
            message=message,
            experiment_id=experiment_id,
            workflows_cancelled=workflows_cancelled,
        )

        experiment_stop_result.additional_properties = d
        return experiment_stop_result

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
