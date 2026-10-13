from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_structure_choices import EvalStructureChoices
    from ..models.eval_structure_config import EvalStructureConfig
    from ..models.eval_structure_config_params_desc import EvalStructureConfigParamsDesc
    from ..models.eval_structure_config_params_option import (
        EvalStructureConfigParamsOption,
    )
    from ..models.eval_structure_function_params_schema import (
        EvalStructureFunctionParamsSchema,
    )
    from ..models.eval_structure_mapping import EvalStructureMapping
    from ..models.eval_structure_models import EvalStructureModels
    from ..models.eval_structure_output import EvalStructureOutput
    from ..models.eval_structure_params import EvalStructureParams
    from ..models.eval_structure_run_config import EvalStructureRunConfig


T = TypeVar("T", bound="EvalStructure")


@_attrs_define
class EvalStructure:
    """
    Attributes:
        id (UUID):
        template_id (UUID):
        name (str):
        description (str | Unset):
        eval_tags (list[str] | Unset):
        template_name (str | Unset):
        required_keys (list[str] | Unset):
        optional_keys (list[str] | Unset):
        variable_keys (list[str] | Unset):
        run_prompt_column (bool | Unset):
        mapping (EvalStructureMapping | Unset):
        config (EvalStructureConfig | Unset):
        params (EvalStructureParams | Unset):
        function_params_schema (EvalStructureFunctionParamsSchema | Unset):
        eval_type_id (str | Unset):
        eval_type (str | Unset):
        reason_column (bool | Unset):
        models (EvalStructureModels | Unset):
        selected_model (str | Unset):
        output (EvalStructureOutput | Unset):
        config_params_desc (EvalStructureConfigParamsDesc | Unset):
        config_params_option (EvalStructureConfigParamsOption | Unset):
        kb_id (None | Unset | UUID):
        error_localizer (bool | Unset):
        choices (EvalStructureChoices | Unset):
        api_key_available (bool | Unset):
        run_config (EvalStructureRunConfig | Unset):
    """

    id: UUID
    template_id: UUID
    name: str
    description: str | Unset = UNSET
    eval_tags: list[str] | Unset = UNSET
    template_name: str | Unset = UNSET
    required_keys: list[str] | Unset = UNSET
    optional_keys: list[str] | Unset = UNSET
    variable_keys: list[str] | Unset = UNSET
    run_prompt_column: bool | Unset = UNSET
    mapping: EvalStructureMapping | Unset = UNSET
    config: EvalStructureConfig | Unset = UNSET
    params: EvalStructureParams | Unset = UNSET
    function_params_schema: EvalStructureFunctionParamsSchema | Unset = UNSET
    eval_type_id: str | Unset = UNSET
    eval_type: str | Unset = UNSET
    reason_column: bool | Unset = UNSET
    models: EvalStructureModels | Unset = UNSET
    selected_model: str | Unset = UNSET
    output: EvalStructureOutput | Unset = UNSET
    config_params_desc: EvalStructureConfigParamsDesc | Unset = UNSET
    config_params_option: EvalStructureConfigParamsOption | Unset = UNSET
    kb_id: None | Unset | UUID = UNSET
    error_localizer: bool | Unset = UNSET
    choices: EvalStructureChoices | Unset = UNSET
    api_key_available: bool | Unset = UNSET
    run_config: EvalStructureRunConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        template_id = str(self.template_id)

        name = self.name

        description = self.description

        eval_tags: list[str] | Unset = UNSET
        if not isinstance(self.eval_tags, Unset):
            eval_tags = self.eval_tags

        template_name = self.template_name

        required_keys: list[str] | Unset = UNSET
        if not isinstance(self.required_keys, Unset):
            required_keys = self.required_keys

        optional_keys: list[str] | Unset = UNSET
        if not isinstance(self.optional_keys, Unset):
            optional_keys = self.optional_keys

        variable_keys: list[str] | Unset = UNSET
        if not isinstance(self.variable_keys, Unset):
            variable_keys = self.variable_keys

        run_prompt_column = self.run_prompt_column

        mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mapping, Unset):
            mapping = self.mapping.to_dict()

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.params, Unset):
            params = self.params.to_dict()

        function_params_schema: dict[str, Any] | Unset = UNSET
        if not isinstance(self.function_params_schema, Unset):
            function_params_schema = self.function_params_schema.to_dict()

        eval_type_id = self.eval_type_id

        eval_type = self.eval_type

        reason_column = self.reason_column

        models: dict[str, Any] | Unset = UNSET
        if not isinstance(self.models, Unset):
            models = self.models.to_dict()

        selected_model = self.selected_model

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        config_params_desc: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_params_desc, Unset):
            config_params_desc = self.config_params_desc.to_dict()

        config_params_option: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_params_option, Unset):
            config_params_option = self.config_params_option.to_dict()

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        error_localizer = self.error_localizer

        choices: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = self.choices.to_dict()

        api_key_available = self.api_key_available

        run_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run_config, Unset):
            run_config = self.run_config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "template_id": template_id,
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if eval_tags is not UNSET:
            field_dict["eval_tags"] = eval_tags
        if template_name is not UNSET:
            field_dict["template_name"] = template_name
        if required_keys is not UNSET:
            field_dict["required_keys"] = required_keys
        if optional_keys is not UNSET:
            field_dict["optional_keys"] = optional_keys
        if variable_keys is not UNSET:
            field_dict["variable_keys"] = variable_keys
        if run_prompt_column is not UNSET:
            field_dict["run_prompt_column"] = run_prompt_column
        if mapping is not UNSET:
            field_dict["mapping"] = mapping
        if config is not UNSET:
            field_dict["config"] = config
        if params is not UNSET:
            field_dict["params"] = params
        if function_params_schema is not UNSET:
            field_dict["function_params_schema"] = function_params_schema
        if eval_type_id is not UNSET:
            field_dict["eval_type_id"] = eval_type_id
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if reason_column is not UNSET:
            field_dict["reason_column"] = reason_column
        if models is not UNSET:
            field_dict["models"] = models
        if selected_model is not UNSET:
            field_dict["selected_model"] = selected_model
        if output is not UNSET:
            field_dict["output"] = output
        if config_params_desc is not UNSET:
            field_dict["config_params_desc"] = config_params_desc
        if config_params_option is not UNSET:
            field_dict["config_params_option"] = config_params_option
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if choices is not UNSET:
            field_dict["choices"] = choices
        if api_key_available is not UNSET:
            field_dict["api_key_available"] = api_key_available
        if run_config is not UNSET:
            field_dict["run_config"] = run_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_structure_choices import EvalStructureChoices
        from ..models.eval_structure_config import EvalStructureConfig
        from ..models.eval_structure_config_params_desc import (
            EvalStructureConfigParamsDesc,
        )
        from ..models.eval_structure_config_params_option import (
            EvalStructureConfigParamsOption,
        )
        from ..models.eval_structure_function_params_schema import (
            EvalStructureFunctionParamsSchema,
        )
        from ..models.eval_structure_mapping import EvalStructureMapping
        from ..models.eval_structure_models import EvalStructureModels
        from ..models.eval_structure_output import EvalStructureOutput
        from ..models.eval_structure_params import EvalStructureParams
        from ..models.eval_structure_run_config import EvalStructureRunConfig

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        template_id = UUID(d.pop("template_id"))

        name = d.pop("name")

        description = d.pop("description", UNSET)

        eval_tags = cast(list[str], d.pop("eval_tags", UNSET))

        template_name = d.pop("template_name", UNSET)

        required_keys = cast(list[str], d.pop("required_keys", UNSET))

        optional_keys = cast(list[str], d.pop("optional_keys", UNSET))

        variable_keys = cast(list[str], d.pop("variable_keys", UNSET))

        run_prompt_column = d.pop("run_prompt_column", UNSET)

        _mapping = d.pop("mapping", UNSET)
        mapping: EvalStructureMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = EvalStructureMapping.from_dict(_mapping)

        _config = d.pop("config", UNSET)
        config: EvalStructureConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalStructureConfig.from_dict(_config)

        _params = d.pop("params", UNSET)
        params: EvalStructureParams | Unset
        if isinstance(_params, Unset):
            params = UNSET
        else:
            params = EvalStructureParams.from_dict(_params)

        _function_params_schema = d.pop("function_params_schema", UNSET)
        function_params_schema: EvalStructureFunctionParamsSchema | Unset
        if isinstance(_function_params_schema, Unset):
            function_params_schema = UNSET
        else:
            function_params_schema = EvalStructureFunctionParamsSchema.from_dict(
                _function_params_schema
            )

        eval_type_id = d.pop("eval_type_id", UNSET)

        eval_type = d.pop("eval_type", UNSET)

        reason_column = d.pop("reason_column", UNSET)

        _models = d.pop("models", UNSET)
        models: EvalStructureModels | Unset
        if isinstance(_models, Unset):
            models = UNSET
        else:
            models = EvalStructureModels.from_dict(_models)

        selected_model = d.pop("selected_model", UNSET)

        _output = d.pop("output", UNSET)
        output: EvalStructureOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = EvalStructureOutput.from_dict(_output)

        _config_params_desc = d.pop("config_params_desc", UNSET)
        config_params_desc: EvalStructureConfigParamsDesc | Unset
        if isinstance(_config_params_desc, Unset):
            config_params_desc = UNSET
        else:
            config_params_desc = EvalStructureConfigParamsDesc.from_dict(
                _config_params_desc
            )

        _config_params_option = d.pop("config_params_option", UNSET)
        config_params_option: EvalStructureConfigParamsOption | Unset
        if isinstance(_config_params_option, Unset):
            config_params_option = UNSET
        else:
            config_params_option = EvalStructureConfigParamsOption.from_dict(
                _config_params_option
            )

        def _parse_kb_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                kb_id_type_0 = UUID(data)

                return kb_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        kb_id = _parse_kb_id(d.pop("kb_id", UNSET))

        error_localizer = d.pop("error_localizer", UNSET)

        _choices = d.pop("choices", UNSET)
        choices: EvalStructureChoices | Unset
        if isinstance(_choices, Unset):
            choices = UNSET
        else:
            choices = EvalStructureChoices.from_dict(_choices)

        api_key_available = d.pop("api_key_available", UNSET)

        _run_config = d.pop("run_config", UNSET)
        run_config: EvalStructureRunConfig | Unset
        if isinstance(_run_config, Unset):
            run_config = UNSET
        else:
            run_config = EvalStructureRunConfig.from_dict(_run_config)

        eval_structure = cls(
            id=id,
            template_id=template_id,
            name=name,
            description=description,
            eval_tags=eval_tags,
            template_name=template_name,
            required_keys=required_keys,
            optional_keys=optional_keys,
            variable_keys=variable_keys,
            run_prompt_column=run_prompt_column,
            mapping=mapping,
            config=config,
            params=params,
            function_params_schema=function_params_schema,
            eval_type_id=eval_type_id,
            eval_type=eval_type,
            reason_column=reason_column,
            models=models,
            selected_model=selected_model,
            output=output,
            config_params_desc=config_params_desc,
            config_params_option=config_params_option,
            kb_id=kb_id,
            error_localizer=error_localizer,
            choices=choices,
            api_key_available=api_key_available,
            run_config=run_config,
        )

        eval_structure.additional_properties = d
        return eval_structure

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
