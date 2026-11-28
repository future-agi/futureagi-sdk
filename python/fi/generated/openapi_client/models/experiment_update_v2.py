from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_metric_entry import EvalMetricEntry
    from ..models.prompt_config_entry import PromptConfigEntry


T = TypeVar("T", bound="ExperimentUpdateV2")


@_attrs_define
class ExperimentUpdateV2:
    """
    Attributes:
        column_id (None | Unset | UUID):
        prompt_config (list[PromptConfigEntry] | Unset):
        user_eval_metrics (list[EvalMetricEntry] | Unset):
    """

    column_id: None | Unset | UUID = UNSET
    prompt_config: list[PromptConfigEntry] | Unset = UNSET
    user_eval_metrics: list[EvalMetricEntry] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id: None | str | Unset
        if isinstance(self.column_id, Unset):
            column_id = UNSET
        elif isinstance(self.column_id, UUID):
            column_id = str(self.column_id)
        else:
            column_id = self.column_id

        prompt_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.prompt_config, Unset):
            prompt_config = []
            for prompt_config_item_data in self.prompt_config:
                prompt_config_item = prompt_config_item_data.to_dict()
                prompt_config.append(prompt_config_item)

        user_eval_metrics: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.user_eval_metrics, Unset):
            user_eval_metrics = []
            for user_eval_metrics_item_data in self.user_eval_metrics:
                user_eval_metrics_item = user_eval_metrics_item_data.to_dict()
                user_eval_metrics.append(user_eval_metrics_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if column_id is not UNSET:
            field_dict["column_id"] = column_id
        if prompt_config is not UNSET:
            field_dict["prompt_config"] = prompt_config
        if user_eval_metrics is not UNSET:
            field_dict["user_eval_metrics"] = user_eval_metrics

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_metric_entry import EvalMetricEntry
        from ..models.prompt_config_entry import PromptConfigEntry

        d = dict(src_dict)

        def _parse_column_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                column_id_type_0 = UUID(data)

                return column_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        column_id = _parse_column_id(d.pop("column_id", UNSET))

        _prompt_config = d.pop("prompt_config", UNSET)
        prompt_config: list[PromptConfigEntry] | Unset = UNSET
        if _prompt_config is not UNSET:
            prompt_config = []
            for prompt_config_item_data in _prompt_config:
                prompt_config_item = PromptConfigEntry.from_dict(
                    prompt_config_item_data
                )

                prompt_config.append(prompt_config_item)

        _user_eval_metrics = d.pop("user_eval_metrics", UNSET)
        user_eval_metrics: list[EvalMetricEntry] | Unset = UNSET
        if _user_eval_metrics is not UNSET:
            user_eval_metrics = []
            for user_eval_metrics_item_data in _user_eval_metrics:
                user_eval_metrics_item = EvalMetricEntry.from_dict(
                    user_eval_metrics_item_data
                )

                user_eval_metrics.append(user_eval_metrics_item)

        experiment_update_v2 = cls(
            column_id=column_id,
            prompt_config=prompt_config,
            user_eval_metrics=user_eval_metrics,
        )

        experiment_update_v2.additional_properties = d
        return experiment_update_v2

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
