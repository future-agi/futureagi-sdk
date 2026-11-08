from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_config import PromptConfig


T = TypeVar("T", bound="AddRunPrompt")


@_attrs_define
class AddRunPrompt:
    """
    Attributes:
        dataset_id (UUID):
        name (str):
        config (PromptConfig | Unset):
    """

    dataset_id: UUID
    name: str
    config: PromptConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        name = self.name

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "name": name,
            }
        )
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_config import PromptConfig

        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        name = d.pop("name")

        _config = d.pop("config", UNSET)
        config: PromptConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = PromptConfig.from_dict(_config)

        add_run_prompt = cls(
            dataset_id=dataset_id,
            name=name,
            config=config,
        )

        add_run_prompt.additional_properties = d
        return add_run_prompt

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
