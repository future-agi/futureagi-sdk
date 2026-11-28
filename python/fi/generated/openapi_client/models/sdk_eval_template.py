from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_eval_template_choices import SDKEvalTemplateChoices
    from ..models.sdk_eval_template_config import SDKEvalTemplateConfig
    from ..models.sdk_eval_template_criteria import SDKEvalTemplateCriteria
    from ..models.sdk_eval_template_eval_tags import SDKEvalTemplateEvalTags


T = TypeVar("T", bound="SDKEvalTemplate")


@_attrs_define
class SDKEvalTemplate:
    """
    Attributes:
        id (str):
        name (str):
        description (None | str):
        organization (None | str):
        owner (None | str):
        eval_id (None | str):
        eval_tags (SDKEvalTemplateEvalTags | Unset):
        config (SDKEvalTemplateConfig | Unset):
        criteria (SDKEvalTemplateCriteria | Unset):
        choices (SDKEvalTemplateChoices | Unset):
        multi_choice (bool | None | Unset):
    """

    id: str
    name: str
    description: None | str
    organization: None | str
    owner: None | str
    eval_id: None | str
    eval_tags: SDKEvalTemplateEvalTags | Unset = UNSET
    config: SDKEvalTemplateConfig | Unset = UNSET
    criteria: SDKEvalTemplateCriteria | Unset = UNSET
    choices: SDKEvalTemplateChoices | Unset = UNSET
    multi_choice: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        description: None | str
        description = self.description

        organization: None | str
        organization = self.organization

        owner: None | str
        owner = self.owner

        eval_id: None | str
        eval_id = self.eval_id

        eval_tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_tags, Unset):
            eval_tags = self.eval_tags.to_dict()

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        criteria: dict[str, Any] | Unset = UNSET
        if not isinstance(self.criteria, Unset):
            criteria = self.criteria.to_dict()

        choices: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = self.choices.to_dict()

        multi_choice: bool | None | Unset
        if isinstance(self.multi_choice, Unset):
            multi_choice = UNSET
        else:
            multi_choice = self.multi_choice

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "organization": organization,
                "owner": owner,
                "eval_id": eval_id,
            }
        )
        if eval_tags is not UNSET:
            field_dict["eval_tags"] = eval_tags
        if config is not UNSET:
            field_dict["config"] = config
        if criteria is not UNSET:
            field_dict["criteria"] = criteria
        if choices is not UNSET:
            field_dict["choices"] = choices
        if multi_choice is not UNSET:
            field_dict["multi_choice"] = multi_choice

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_eval_template_choices import SDKEvalTemplateChoices
        from ..models.sdk_eval_template_config import SDKEvalTemplateConfig
        from ..models.sdk_eval_template_criteria import SDKEvalTemplateCriteria
        from ..models.sdk_eval_template_eval_tags import SDKEvalTemplateEvalTags

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        def _parse_organization(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        organization = _parse_organization(d.pop("organization"))

        def _parse_owner(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        owner = _parse_owner(d.pop("owner"))

        def _parse_eval_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        eval_id = _parse_eval_id(d.pop("eval_id"))

        _eval_tags = d.pop("eval_tags", UNSET)
        eval_tags: SDKEvalTemplateEvalTags | Unset
        if isinstance(_eval_tags, Unset):
            eval_tags = UNSET
        else:
            eval_tags = SDKEvalTemplateEvalTags.from_dict(_eval_tags)

        _config = d.pop("config", UNSET)
        config: SDKEvalTemplateConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = SDKEvalTemplateConfig.from_dict(_config)

        _criteria = d.pop("criteria", UNSET)
        criteria: SDKEvalTemplateCriteria | Unset
        if isinstance(_criteria, Unset):
            criteria = UNSET
        else:
            criteria = SDKEvalTemplateCriteria.from_dict(_criteria)

        _choices = d.pop("choices", UNSET)
        choices: SDKEvalTemplateChoices | Unset
        if isinstance(_choices, Unset):
            choices = UNSET
        else:
            choices = SDKEvalTemplateChoices.from_dict(_choices)

        def _parse_multi_choice(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        multi_choice = _parse_multi_choice(d.pop("multi_choice", UNSET))

        sdk_eval_template = cls(
            id=id,
            name=name,
            description=description,
            organization=organization,
            owner=owner,
            eval_id=eval_id,
            eval_tags=eval_tags,
            config=config,
            criteria=criteria,
            choices=choices,
            multi_choice=multi_choice,
        )

        sdk_eval_template.additional_properties = d
        return sdk_eval_template

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
