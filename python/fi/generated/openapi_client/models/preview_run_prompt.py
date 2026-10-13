from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_config import PromptConfig


T = TypeVar("T", bound="PreviewRunPrompt")


@_attrs_define
class PreviewRunPrompt:
    """
    Attributes:
        dataset_id (UUID):
        name (str):
        config (PromptConfig | Unset):
        first_n_rows (int | Unset):
        row_indices (list[int] | Unset): List of row indices to preview. Must contain at least one integer.
    """

    dataset_id: UUID
    name: str
    config: PromptConfig | Unset = UNSET
    first_n_rows: int | Unset = UNSET
    row_indices: list[int] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        name = self.name

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        first_n_rows = self.first_n_rows

        row_indices: list[int] | Unset = UNSET
        if not isinstance(self.row_indices, Unset):
            row_indices = self.row_indices

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
        if first_n_rows is not UNSET:
            field_dict["first_n_rows"] = first_n_rows
        if row_indices is not UNSET:
            field_dict["row_indices"] = row_indices

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

        first_n_rows = d.pop("first_n_rows", UNSET)

        row_indices = cast(list[int], d.pop("row_indices", UNSET))

        preview_run_prompt = cls(
            dataset_id=dataset_id,
            name=name,
            config=config,
            first_n_rows=first_n_rows,
            row_indices=row_indices,
        )

        preview_run_prompt.additional_properties = d
        return preview_run_prompt

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
