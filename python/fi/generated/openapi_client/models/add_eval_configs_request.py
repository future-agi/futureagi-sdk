from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_config_definition import EvalConfigDefinition


T = TypeVar("T", bound="AddEvalConfigsRequest")


@_attrs_define
class AddEvalConfigsRequest:
    """
    Attributes:
        evaluations_config (list[EvalConfigDefinition]): Array of evaluation configuration objects to add. At least one
            required.
    """

    evaluations_config: list[EvalConfigDefinition]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        evaluations_config = []
        for evaluations_config_item_data in self.evaluations_config:
            evaluations_config_item = evaluations_config_item_data.to_dict()
            evaluations_config.append(evaluations_config_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "evaluations_config": evaluations_config,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_definition import EvalConfigDefinition

        d = dict(src_dict)
        evaluations_config = []
        _evaluations_config = d.pop("evaluations_config")
        for evaluations_config_item_data in _evaluations_config:
            evaluations_config_item = EvalConfigDefinition.from_dict(
                evaluations_config_item_data
            )

            evaluations_config.append(evaluations_config_item)

        add_eval_configs_request = cls(
            evaluations_config=evaluations_config,
        )

        add_eval_configs_request.additional_properties = d
        return add_eval_configs_request

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
