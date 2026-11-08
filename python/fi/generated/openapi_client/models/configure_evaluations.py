from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.configure_evaluations_config import ConfigureEvaluationsConfig
    from ..models.configure_evaluations_inputs import ConfigureEvaluationsInputs


T = TypeVar("T", bound="ConfigureEvaluations")


@_attrs_define
class ConfigureEvaluations:
    """
    Attributes:
        eval_templates (str):
        inputs (ConfigureEvaluationsInputs):
        model_name (None | str | Unset):
        config (ConfigureEvaluationsConfig | Unset):
    """

    eval_templates: str
    inputs: ConfigureEvaluationsInputs
    model_name: None | str | Unset = UNSET
    config: ConfigureEvaluationsConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_templates = self.eval_templates

        inputs = self.inputs.to_dict()

        model_name: None | str | Unset
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_templates": eval_templates,
                "inputs": inputs,
            }
        )
        if model_name is not UNSET:
            field_dict["model_name"] = model_name
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.configure_evaluations_config import ConfigureEvaluationsConfig
        from ..models.configure_evaluations_inputs import ConfigureEvaluationsInputs

        d = dict(src_dict)
        eval_templates = d.pop("eval_templates")

        inputs = ConfigureEvaluationsInputs.from_dict(d.pop("inputs"))

        def _parse_model_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model_name = _parse_model_name(d.pop("model_name", UNSET))

        _config = d.pop("config", UNSET)
        config: ConfigureEvaluationsConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = ConfigureEvaluationsConfig.from_dict(_config)

        configure_evaluations = cls(
            eval_templates=eval_templates,
            inputs=inputs,
            model_name=model_name,
            config=config,
        )

        configure_evaluations.additional_properties = d
        return configure_evaluations

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
