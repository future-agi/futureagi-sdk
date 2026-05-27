from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_response import EvalConfigResponse


T = TypeVar("T", bound="AddEvalConfigsResponse")


@_attrs_define
class AddEvalConfigsResponse:
    """
    Attributes:
        message (str):
        created_eval_configs (list[EvalConfigResponse]):
        run_test_id (UUID):
        warnings (list[str] | Unset): Non-fatal issues encountered while processing individual configs.
    """

    message: str
    created_eval_configs: list[EvalConfigResponse]
    run_test_id: UUID
    warnings: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        created_eval_configs = []
        for created_eval_configs_item_data in self.created_eval_configs:
            created_eval_configs_item = created_eval_configs_item_data.to_dict()
            created_eval_configs.append(created_eval_configs_item)

        run_test_id = str(self.run_test_id)

        warnings: list[str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "created_eval_configs": created_eval_configs,
                "run_test_id": run_test_id,
            }
        )
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_response import EvalConfigResponse

        d = dict(src_dict)
        message = d.pop("message")

        created_eval_configs = []
        _created_eval_configs = d.pop("created_eval_configs")
        for created_eval_configs_item_data in _created_eval_configs:
            created_eval_configs_item = EvalConfigResponse.from_dict(
                created_eval_configs_item_data
            )

            created_eval_configs.append(created_eval_configs_item)

        run_test_id = UUID(d.pop("run_test_id"))

        warnings = cast(list[str], d.pop("warnings", UNSET))

        add_eval_configs_response = cls(
            message=message,
            created_eval_configs=created_eval_configs,
            run_test_id=run_test_id,
            warnings=warnings,
        )

        add_eval_configs_response.additional_properties = d
        return add_eval_configs_response

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
