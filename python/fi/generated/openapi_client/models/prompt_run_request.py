from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_run_configuration import PromptRunConfiguration
    from ..models.prompt_run_request_evaluation_configs_item_type_4_type_0 import (
        PromptRunRequestEvaluationConfigsItemType4Type0,
    )
    from ..models.prompt_run_request_is_run_type_4_type_0 import (
        PromptRunRequestIsRunType4Type0,
    )
    from ..models.prompt_run_request_placeholders_type_4_type_0 import (
        PromptRunRequestPlaceholdersType4Type0,
    )
    from ..models.prompt_run_request_variable_names import PromptRunRequestVariableNames


T = TypeVar("T", bound="PromptRunRequest")


@_attrs_define
class PromptRunRequest:
    """
    Attributes:
        name (str | Unset):
        version (str | Unset):
        prompt_config (list[PromptRunConfiguration] | Unset):
        variable_names (PromptRunRequestVariableNames | Unset):
        placeholders (bool | float | list[Any] | None | PromptRunRequestPlaceholdersType4Type0 | str | Unset): Any valid
            JSON value.
        evaluation_configs (list[bool | float | list[Any] | None | PromptRunRequestEvaluationConfigsItemType4Type0 |
            str] | Unset):
        source (str | Unset):
        is_run (bool | float | list[Any] | None | PromptRunRequestIsRunType4Type0 | str | Unset): Any valid JSON value.
        is_sdk (bool | Unset):
        run_index (int | None | Unset):
    """

    name: str | Unset = UNSET
    version: str | Unset = UNSET
    prompt_config: list[PromptRunConfiguration] | Unset = UNSET
    variable_names: PromptRunRequestVariableNames | Unset = UNSET
    placeholders: (
        bool
        | float
        | list[Any]
        | None
        | PromptRunRequestPlaceholdersType4Type0
        | str
        | Unset
    ) = UNSET
    evaluation_configs: (
        list[
            bool
            | float
            | list[Any]
            | None
            | PromptRunRequestEvaluationConfigsItemType4Type0
            | str
        ]
        | Unset
    ) = UNSET
    source: str | Unset = UNSET
    is_run: (
        bool | float | list[Any] | None | PromptRunRequestIsRunType4Type0 | str | Unset
    ) = UNSET
    is_sdk: bool | Unset = UNSET
    run_index: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.prompt_run_request_evaluation_configs_item_type_4_type_0 import (
            PromptRunRequestEvaluationConfigsItemType4Type0,
        )
        from ..models.prompt_run_request_is_run_type_4_type_0 import (
            PromptRunRequestIsRunType4Type0,
        )
        from ..models.prompt_run_request_placeholders_type_4_type_0 import (
            PromptRunRequestPlaceholdersType4Type0,
        )

        name = self.name

        version = self.version

        prompt_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.prompt_config, Unset):
            prompt_config = []
            for prompt_config_item_data in self.prompt_config:
                prompt_config_item = prompt_config_item_data.to_dict()
                prompt_config.append(prompt_config_item)

        variable_names: dict[str, Any] | Unset = UNSET
        if not isinstance(self.variable_names, Unset):
            variable_names = self.variable_names.to_dict()

        placeholders: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.placeholders, Unset):
            placeholders = UNSET
        elif isinstance(self.placeholders, list):
            placeholders = self.placeholders

        elif isinstance(self.placeholders, PromptRunRequestPlaceholdersType4Type0):
            placeholders = self.placeholders.to_dict()
        else:
            placeholders = self.placeholders

        evaluation_configs: (
            list[bool | dict[str, Any] | float | list[Any] | None | str] | Unset
        ) = UNSET
        if not isinstance(self.evaluation_configs, Unset):
            evaluation_configs = []
            for evaluation_configs_item_data in self.evaluation_configs:
                evaluation_configs_item: (
                    bool | dict[str, Any] | float | list[Any] | None | str
                )
                if isinstance(evaluation_configs_item_data, list):
                    evaluation_configs_item = evaluation_configs_item_data

                elif isinstance(
                    evaluation_configs_item_data,
                    PromptRunRequestEvaluationConfigsItemType4Type0,
                ):
                    evaluation_configs_item = evaluation_configs_item_data.to_dict()
                else:
                    evaluation_configs_item = evaluation_configs_item_data
                evaluation_configs.append(evaluation_configs_item)

        source = self.source

        is_run: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.is_run, Unset):
            is_run = UNSET
        elif isinstance(self.is_run, list):
            is_run = self.is_run

        elif isinstance(self.is_run, PromptRunRequestIsRunType4Type0):
            is_run = self.is_run.to_dict()
        else:
            is_run = self.is_run

        is_sdk = self.is_sdk

        run_index: int | None | Unset
        if isinstance(self.run_index, Unset):
            run_index = UNSET
        else:
            run_index = self.run_index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if version is not UNSET:
            field_dict["version"] = version
        if prompt_config is not UNSET:
            field_dict["prompt_config"] = prompt_config
        if variable_names is not UNSET:
            field_dict["variable_names"] = variable_names
        if placeholders is not UNSET:
            field_dict["placeholders"] = placeholders
        if evaluation_configs is not UNSET:
            field_dict["evaluation_configs"] = evaluation_configs
        if source is not UNSET:
            field_dict["source"] = source
        if is_run is not UNSET:
            field_dict["is_run"] = is_run
        if is_sdk is not UNSET:
            field_dict["is_sdk"] = is_sdk
        if run_index is not UNSET:
            field_dict["run_index"] = run_index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_run_configuration import PromptRunConfiguration
        from ..models.prompt_run_request_evaluation_configs_item_type_4_type_0 import (
            PromptRunRequestEvaluationConfigsItemType4Type0,
        )
        from ..models.prompt_run_request_is_run_type_4_type_0 import (
            PromptRunRequestIsRunType4Type0,
        )
        from ..models.prompt_run_request_placeholders_type_4_type_0 import (
            PromptRunRequestPlaceholdersType4Type0,
        )
        from ..models.prompt_run_request_variable_names import (
            PromptRunRequestVariableNames,
        )

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        version = d.pop("version", UNSET)

        _prompt_config = d.pop("prompt_config", UNSET)
        prompt_config: list[PromptRunConfiguration] | Unset = UNSET
        if _prompt_config is not UNSET:
            prompt_config = []
            for prompt_config_item_data in _prompt_config:
                prompt_config_item = PromptRunConfiguration.from_dict(
                    prompt_config_item_data
                )

                prompt_config.append(prompt_config_item)

        _variable_names = d.pop("variable_names", UNSET)
        variable_names: PromptRunRequestVariableNames | Unset
        if isinstance(_variable_names, Unset):
            variable_names = UNSET
        else:
            variable_names = PromptRunRequestVariableNames.from_dict(_variable_names)

        def _parse_placeholders(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | PromptRunRequestPlaceholdersType4Type0
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                placeholders_type_3 = cast(list[Any], data)

                return placeholders_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                placeholders_type_4_type_0 = (
                    PromptRunRequestPlaceholdersType4Type0.from_dict(data)
                )

                return placeholders_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | PromptRunRequestPlaceholdersType4Type0
                | str
                | Unset,
                data,
            )

        placeholders = _parse_placeholders(d.pop("placeholders", UNSET))

        _evaluation_configs = d.pop("evaluation_configs", UNSET)
        evaluation_configs: (
            list[
                bool
                | float
                | list[Any]
                | None
                | PromptRunRequestEvaluationConfigsItemType4Type0
                | str
            ]
            | Unset
        ) = UNSET
        if _evaluation_configs is not UNSET:
            evaluation_configs = []
            for evaluation_configs_item_data in _evaluation_configs:

                def _parse_evaluation_configs_item(
                    data: object,
                ) -> (
                    bool
                    | float
                    | list[Any]
                    | None
                    | PromptRunRequestEvaluationConfigsItemType4Type0
                    | str
                ):
                    if data is None:
                        return data
                    try:
                        if not isinstance(data, list):
                            raise TypeError()
                        evaluation_configs_item_type_3 = cast(list[Any], data)

                        return evaluation_configs_item_type_3
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        evaluation_configs_item_type_4_type_0 = (
                            PromptRunRequestEvaluationConfigsItemType4Type0.from_dict(
                                data
                            )
                        )

                        return evaluation_configs_item_type_4_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    return cast(
                        bool
                        | float
                        | list[Any]
                        | None
                        | PromptRunRequestEvaluationConfigsItemType4Type0
                        | str,
                        data,
                    )

                evaluation_configs_item = _parse_evaluation_configs_item(
                    evaluation_configs_item_data
                )

                evaluation_configs.append(evaluation_configs_item)

        source = d.pop("source", UNSET)

        def _parse_is_run(
            data: object,
        ) -> (
            bool
            | float
            | list[Any]
            | None
            | PromptRunRequestIsRunType4Type0
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                is_run_type_3 = cast(list[Any], data)

                return is_run_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                is_run_type_4_type_0 = PromptRunRequestIsRunType4Type0.from_dict(data)

                return is_run_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | float
                | list[Any]
                | None
                | PromptRunRequestIsRunType4Type0
                | str
                | Unset,
                data,
            )

        is_run = _parse_is_run(d.pop("is_run", UNSET))

        is_sdk = d.pop("is_sdk", UNSET)

        def _parse_run_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        run_index = _parse_run_index(d.pop("run_index", UNSET))

        prompt_run_request = cls(
            name=name,
            version=version,
            prompt_config=prompt_config,
            variable_names=variable_names,
            placeholders=placeholders,
            evaluation_configs=evaluation_configs,
            source=source,
            is_run=is_run,
            is_sdk=is_sdk,
            run_index=run_index,
        )

        prompt_run_request.additional_properties = d
        return prompt_run_request

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
