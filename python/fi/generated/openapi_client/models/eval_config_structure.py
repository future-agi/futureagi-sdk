from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_structure_config import EvalConfigStructureConfig
    from ..models.eval_config_structure_config_params_desc import (
        EvalConfigStructureConfigParamsDesc,
    )
    from ..models.eval_config_structure_config_params_option import (
        EvalConfigStructureConfigParamsOption,
    )
    from ..models.eval_config_structure_eval_tags import EvalConfigStructureEvalTags
    from ..models.eval_config_structure_function_params_schema import (
        EvalConfigStructureFunctionParamsSchema,
    )
    from ..models.eval_config_structure_mapping import EvalConfigStructureMapping
    from ..models.eval_config_structure_models import EvalConfigStructureModels
    from ..models.eval_config_structure_output import EvalConfigStructureOutput
    from ..models.eval_config_structure_params import EvalConfigStructureParams


T = TypeVar("T", bound="EvalConfigStructure")


@_attrs_define
class EvalConfigStructure:
    """
    Attributes:
        required_keys (list[str]):
        optional_keys (list[str]):
        variable_keys (list[str]):
        id (UUID | Unset):
        template_id (UUID | Unset):
        name (str | Unset):
        reason_column (bool | Unset):
        eval_tags (EvalConfigStructureEvalTags | Unset):
        description (str | Unset):
        run_prompt_column (bool | Unset):
        template_name (str | Unset):
        mapping (EvalConfigStructureMapping | Unset):
        config (EvalConfigStructureConfig | Unset):
        params (EvalConfigStructureParams | Unset):
        function_params_schema (EvalConfigStructureFunctionParamsSchema | Unset):
        models (EvalConfigStructureModels | Unset):
        selected_model (None | str | Unset):
        error_localizer (bool | Unset):
        kb_id (None | Unset | UUID):
        output (EvalConfigStructureOutput | Unset):
        config_params_desc (EvalConfigStructureConfigParamsDesc | Unset):
        config_params_option (EvalConfigStructureConfigParamsOption | Unset):
        api_key_available (bool | Unset):
    """

    required_keys: list[str]
    optional_keys: list[str]
    variable_keys: list[str]
    id: UUID | Unset = UNSET
    template_id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    reason_column: bool | Unset = UNSET
    eval_tags: EvalConfigStructureEvalTags | Unset = UNSET
    description: str | Unset = UNSET
    run_prompt_column: bool | Unset = UNSET
    template_name: str | Unset = UNSET
    mapping: EvalConfigStructureMapping | Unset = UNSET
    config: EvalConfigStructureConfig | Unset = UNSET
    params: EvalConfigStructureParams | Unset = UNSET
    function_params_schema: EvalConfigStructureFunctionParamsSchema | Unset = UNSET
    models: EvalConfigStructureModels | Unset = UNSET
    selected_model: None | str | Unset = UNSET
    error_localizer: bool | Unset = UNSET
    kb_id: None | Unset | UUID = UNSET
    output: EvalConfigStructureOutput | Unset = UNSET
    config_params_desc: EvalConfigStructureConfigParamsDesc | Unset = UNSET
    config_params_option: EvalConfigStructureConfigParamsOption | Unset = UNSET
    api_key_available: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        required_keys = self.required_keys

        optional_keys = self.optional_keys

        variable_keys = self.variable_keys

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        template_id: str | Unset = UNSET
        if not isinstance(self.template_id, Unset):
            template_id = str(self.template_id)

        name = self.name

        reason_column = self.reason_column

        eval_tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_tags, Unset):
            eval_tags = self.eval_tags.to_dict()

        description = self.description

        run_prompt_column = self.run_prompt_column

        template_name = self.template_name

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

        models: dict[str, Any] | Unset = UNSET
        if not isinstance(self.models, Unset):
            models = self.models.to_dict()

        selected_model: None | str | Unset
        if isinstance(self.selected_model, Unset):
            selected_model = UNSET
        else:
            selected_model = self.selected_model

        error_localizer = self.error_localizer

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        config_params_desc: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_params_desc, Unset):
            config_params_desc = self.config_params_desc.to_dict()

        config_params_option: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_params_option, Unset):
            config_params_option = self.config_params_option.to_dict()

        api_key_available = self.api_key_available

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "required_keys": required_keys,
                "optional_keys": optional_keys,
                "variable_keys": variable_keys,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if template_id is not UNSET:
            field_dict["template_id"] = template_id
        if name is not UNSET:
            field_dict["name"] = name
        if reason_column is not UNSET:
            field_dict["reason_column"] = reason_column
        if eval_tags is not UNSET:
            field_dict["eval_tags"] = eval_tags
        if description is not UNSET:
            field_dict["description"] = description
        if run_prompt_column is not UNSET:
            field_dict["run_prompt_column"] = run_prompt_column
        if template_name is not UNSET:
            field_dict["template_name"] = template_name
        if mapping is not UNSET:
            field_dict["mapping"] = mapping
        if config is not UNSET:
            field_dict["config"] = config
        if params is not UNSET:
            field_dict["params"] = params
        if function_params_schema is not UNSET:
            field_dict["function_params_schema"] = function_params_schema
        if models is not UNSET:
            field_dict["models"] = models
        if selected_model is not UNSET:
            field_dict["selected_model"] = selected_model
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if output is not UNSET:
            field_dict["output"] = output
        if config_params_desc is not UNSET:
            field_dict["config_params_desc"] = config_params_desc
        if config_params_option is not UNSET:
            field_dict["config_params_option"] = config_params_option
        if api_key_available is not UNSET:
            field_dict["api_key_available"] = api_key_available

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_structure_config import EvalConfigStructureConfig
        from ..models.eval_config_structure_config_params_desc import (
            EvalConfigStructureConfigParamsDesc,
        )
        from ..models.eval_config_structure_config_params_option import (
            EvalConfigStructureConfigParamsOption,
        )
        from ..models.eval_config_structure_eval_tags import EvalConfigStructureEvalTags
        from ..models.eval_config_structure_function_params_schema import (
            EvalConfigStructureFunctionParamsSchema,
        )
        from ..models.eval_config_structure_mapping import EvalConfigStructureMapping
        from ..models.eval_config_structure_models import EvalConfigStructureModels
        from ..models.eval_config_structure_output import EvalConfigStructureOutput
        from ..models.eval_config_structure_params import EvalConfigStructureParams

        d = dict(src_dict)
        required_keys = cast(list[str], d.pop("required_keys"))

        optional_keys = cast(list[str], d.pop("optional_keys"))

        variable_keys = cast(list[str], d.pop("variable_keys"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _template_id = d.pop("template_id", UNSET)
        template_id: UUID | Unset
        if isinstance(_template_id, Unset):
            template_id = UNSET
        else:
            template_id = UUID(_template_id)

        name = d.pop("name", UNSET)

        reason_column = d.pop("reason_column", UNSET)

        _eval_tags = d.pop("eval_tags", UNSET)
        eval_tags: EvalConfigStructureEvalTags | Unset
        if isinstance(_eval_tags, Unset):
            eval_tags = UNSET
        else:
            eval_tags = EvalConfigStructureEvalTags.from_dict(_eval_tags)

        description = d.pop("description", UNSET)

        run_prompt_column = d.pop("run_prompt_column", UNSET)

        template_name = d.pop("template_name", UNSET)

        _mapping = d.pop("mapping", UNSET)
        mapping: EvalConfigStructureMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = EvalConfigStructureMapping.from_dict(_mapping)

        _config = d.pop("config", UNSET)
        config: EvalConfigStructureConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalConfigStructureConfig.from_dict(_config)

        _params = d.pop("params", UNSET)
        params: EvalConfigStructureParams | Unset
        if isinstance(_params, Unset):
            params = UNSET
        else:
            params = EvalConfigStructureParams.from_dict(_params)

        _function_params_schema = d.pop("function_params_schema", UNSET)
        function_params_schema: EvalConfigStructureFunctionParamsSchema | Unset
        if isinstance(_function_params_schema, Unset):
            function_params_schema = UNSET
        else:
            function_params_schema = EvalConfigStructureFunctionParamsSchema.from_dict(
                _function_params_schema
            )

        _models = d.pop("models", UNSET)
        models: EvalConfigStructureModels | Unset
        if isinstance(_models, Unset):
            models = UNSET
        else:
            models = EvalConfigStructureModels.from_dict(_models)

        def _parse_selected_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        selected_model = _parse_selected_model(d.pop("selected_model", UNSET))

        error_localizer = d.pop("error_localizer", UNSET)

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

        _output = d.pop("output", UNSET)
        output: EvalConfigStructureOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = EvalConfigStructureOutput.from_dict(_output)

        _config_params_desc = d.pop("config_params_desc", UNSET)
        config_params_desc: EvalConfigStructureConfigParamsDesc | Unset
        if isinstance(_config_params_desc, Unset):
            config_params_desc = UNSET
        else:
            config_params_desc = EvalConfigStructureConfigParamsDesc.from_dict(
                _config_params_desc
            )

        _config_params_option = d.pop("config_params_option", UNSET)
        config_params_option: EvalConfigStructureConfigParamsOption | Unset
        if isinstance(_config_params_option, Unset):
            config_params_option = UNSET
        else:
            config_params_option = EvalConfigStructureConfigParamsOption.from_dict(
                _config_params_option
            )

        api_key_available = d.pop("api_key_available", UNSET)

        eval_config_structure = cls(
            required_keys=required_keys,
            optional_keys=optional_keys,
            variable_keys=variable_keys,
            id=id,
            template_id=template_id,
            name=name,
            reason_column=reason_column,
            eval_tags=eval_tags,
            description=description,
            run_prompt_column=run_prompt_column,
            template_name=template_name,
            mapping=mapping,
            config=config,
            params=params,
            function_params_schema=function_params_schema,
            models=models,
            selected_model=selected_model,
            error_localizer=error_localizer,
            kb_id=kb_id,
            output=output,
            config_params_desc=config_params_desc,
            config_params_option=config_params_option,
            api_key_available=api_key_available,
        )

        eval_config_structure.additional_properties = d
        return eval_config_structure

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
