from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_template_detail_response_result_choice_scores import (
        EvalTemplateDetailResponseResultChoiceScores,
    )
    from ..models.eval_template_detail_response_result_choices import (
        EvalTemplateDetailResponseResultChoices,
    )
    from ..models.eval_template_detail_response_result_config import (
        EvalTemplateDetailResponseResultConfig,
    )


T = TypeVar("T", bound="EvalTemplateDetailResponseResult")


@_attrs_define
class EvalTemplateDetailResponseResult:
    """
    Attributes:
        id (UUID):
        name (str):
        template_type (str):
        eval_type (str):
        output_type (str):
        pass_threshold (float):
        multi_choice (bool):
        required_keys (list[str]):
        owner (str):
        created_by_name (str):
        version_count (int):
        current_version (str):
        tags (list[str]):
        check_internet (bool):
        error_localizer_enabled (bool):
        template_format (str):
        aggregation_enabled (bool):
        aggregation_function (str):
        created_at (str):
        updated_at (str):
        description (None | str | Unset):
        instructions (None | str | Unset):
        model (None | str | Unset):
        choice_scores (EvalTemplateDetailResponseResultChoiceScores | Unset):
        choices (EvalTemplateDetailResponseResultChoices | Unset):
        code (None | str | Unset):
        code_language (None | str | Unset):
        composite_child_axis (str | Unset):
        config (EvalTemplateDetailResponseResultConfig | Unset):
    """

    id: UUID
    name: str
    template_type: str
    eval_type: str
    output_type: str
    pass_threshold: float
    multi_choice: bool
    required_keys: list[str]
    owner: str
    created_by_name: str
    version_count: int
    current_version: str
    tags: list[str]
    check_internet: bool
    error_localizer_enabled: bool
    template_format: str
    aggregation_enabled: bool
    aggregation_function: str
    created_at: str
    updated_at: str
    description: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    model: None | str | Unset = UNSET
    choice_scores: EvalTemplateDetailResponseResultChoiceScores | Unset = UNSET
    choices: EvalTemplateDetailResponseResultChoices | Unset = UNSET
    code: None | str | Unset = UNSET
    code_language: None | str | Unset = UNSET
    composite_child_axis: str | Unset = UNSET
    config: EvalTemplateDetailResponseResultConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        template_type = self.template_type

        eval_type = self.eval_type

        output_type = self.output_type

        pass_threshold = self.pass_threshold

        multi_choice = self.multi_choice

        required_keys = self.required_keys

        owner = self.owner

        created_by_name = self.created_by_name

        version_count = self.version_count

        current_version = self.current_version

        tags = self.tags

        check_internet = self.check_internet

        error_localizer_enabled = self.error_localizer_enabled

        template_format = self.template_format

        aggregation_enabled = self.aggregation_enabled

        aggregation_function = self.aggregation_function

        created_at = self.created_at

        updated_at = self.updated_at

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        instructions: None | str | Unset
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        else:
            instructions = self.instructions

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        choice_scores: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choice_scores, Unset):
            choice_scores = self.choice_scores.to_dict()

        choices: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = self.choices.to_dict()

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        code_language: None | str | Unset
        if isinstance(self.code_language, Unset):
            code_language = UNSET
        else:
            code_language = self.code_language

        composite_child_axis = self.composite_child_axis

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "template_type": template_type,
                "eval_type": eval_type,
                "output_type": output_type,
                "pass_threshold": pass_threshold,
                "multi_choice": multi_choice,
                "required_keys": required_keys,
                "owner": owner,
                "created_by_name": created_by_name,
                "version_count": version_count,
                "current_version": current_version,
                "tags": tags,
                "check_internet": check_internet,
                "error_localizer_enabled": error_localizer_enabled,
                "template_format": template_format,
                "aggregation_enabled": aggregation_enabled,
                "aggregation_function": aggregation_function,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if model is not UNSET:
            field_dict["model"] = model
        if choice_scores is not UNSET:
            field_dict["choice_scores"] = choice_scores
        if choices is not UNSET:
            field_dict["choices"] = choices
        if code is not UNSET:
            field_dict["code"] = code
        if code_language is not UNSET:
            field_dict["code_language"] = code_language
        if composite_child_axis is not UNSET:
            field_dict["composite_child_axis"] = composite_child_axis
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_detail_response_result_choice_scores import (
            EvalTemplateDetailResponseResultChoiceScores,
        )
        from ..models.eval_template_detail_response_result_choices import (
            EvalTemplateDetailResponseResultChoices,
        )
        from ..models.eval_template_detail_response_result_config import (
            EvalTemplateDetailResponseResultConfig,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        template_type = d.pop("template_type")

        eval_type = d.pop("eval_type")

        output_type = d.pop("output_type")

        pass_threshold = d.pop("pass_threshold")

        multi_choice = d.pop("multi_choice")

        required_keys = cast(list[str], d.pop("required_keys"))

        owner = d.pop("owner")

        created_by_name = d.pop("created_by_name")

        version_count = d.pop("version_count")

        current_version = d.pop("current_version")

        tags = cast(list[str], d.pop("tags"))

        check_internet = d.pop("check_internet")

        error_localizer_enabled = d.pop("error_localizer_enabled")

        template_format = d.pop("template_format")

        aggregation_enabled = d.pop("aggregation_enabled")

        aggregation_function = d.pop("aggregation_function")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_instructions(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _choice_scores = d.pop("choice_scores", UNSET)
        choice_scores: EvalTemplateDetailResponseResultChoiceScores | Unset
        if isinstance(_choice_scores, Unset):
            choice_scores = UNSET
        else:
            choice_scores = EvalTemplateDetailResponseResultChoiceScores.from_dict(
                _choice_scores
            )

        _choices = d.pop("choices", UNSET)
        choices: EvalTemplateDetailResponseResultChoices | Unset
        if isinstance(_choices, Unset):
            choices = UNSET
        else:
            choices = EvalTemplateDetailResponseResultChoices.from_dict(_choices)

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        def _parse_code_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code_language = _parse_code_language(d.pop("code_language", UNSET))

        composite_child_axis = d.pop("composite_child_axis", UNSET)

        _config = d.pop("config", UNSET)
        config: EvalTemplateDetailResponseResultConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalTemplateDetailResponseResultConfig.from_dict(_config)

        eval_template_detail_response_result = cls(
            id=id,
            name=name,
            template_type=template_type,
            eval_type=eval_type,
            output_type=output_type,
            pass_threshold=pass_threshold,
            multi_choice=multi_choice,
            required_keys=required_keys,
            owner=owner,
            created_by_name=created_by_name,
            version_count=version_count,
            current_version=current_version,
            tags=tags,
            check_internet=check_internet,
            error_localizer_enabled=error_localizer_enabled,
            template_format=template_format,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            instructions=instructions,
            model=model,
            choice_scores=choice_scores,
            choices=choices,
            code=code,
            code_language=code_language,
            composite_child_axis=composite_child_axis,
            config=config,
        )

        eval_template_detail_response_result.additional_properties = d
        return eval_template_detail_response_result

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
