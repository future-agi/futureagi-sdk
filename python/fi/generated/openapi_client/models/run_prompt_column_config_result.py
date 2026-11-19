from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_prompt_column_config_result_config import (
        RunPromptColumnConfigResultConfig,
    )


T = TypeVar("T", bound="RunPromptColumnConfigResult")


@_attrs_define
class RunPromptColumnConfigResult:
    """
    Attributes:
        config (RunPromptColumnConfigResultConfig):
    """

    config: RunPromptColumnConfigResultConfig
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config = self.config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "config": config,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_prompt_column_config_result_config import (
            RunPromptColumnConfigResultConfig,
        )

        d = dict(src_dict)
        config = RunPromptColumnConfigResultConfig.from_dict(d.pop("config"))

        run_prompt_column_config_result = cls(
            config=config,
        )

        run_prompt_column_config_result.additional_properties = d
        return run_prompt_column_config_result

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
