from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_definition_config import EvalConfigDefinitionConfig
    from ..models.eval_config_definition_filters_item import (
        EvalConfigDefinitionFiltersItem,
    )
    from ..models.eval_config_definition_mapping import EvalConfigDefinitionMapping


T = TypeVar("T", bound="EvalConfigDefinition")


@_attrs_define
class EvalConfigDefinition:
    """
    Attributes:
        template_id (UUID): UUID of the evaluation template to use.
        name (str | Unset): Name for this evaluation configuration. Defaults to 'Eval-<template_id>' if omitted.
        config (EvalConfigDefinitionConfig | Unset): Template-specific configuration parameters.
        mapping (EvalConfigDefinitionMapping | Unset): Maps test execution data fields to the evaluation template's
            expected inputs.
        filters (list[EvalConfigDefinitionFiltersItem] | Unset): Canonical filter list to restrict which test results
            are evaluated.
        error_localizer (bool | Unset): Enables granular error localization on evaluation failures. Default: False.
        model (None | str | Unset): Model to use for running this evaluation.
        kb_id (None | Unset | UUID): Knowledge base file to use for this evaluation.
        eval_group (None | Unset | UUID): Eval group that created this evaluation config.
    """

    template_id: UUID
    name: str | Unset = UNSET
    config: EvalConfigDefinitionConfig | Unset = UNSET
    mapping: EvalConfigDefinitionMapping | Unset = UNSET
    filters: list[EvalConfigDefinitionFiltersItem] | Unset = UNSET
    error_localizer: bool | Unset = False
    model: None | str | Unset = UNSET
    kb_id: None | Unset | UUID = UNSET
    eval_group: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = str(self.template_id)

        name = self.name

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mapping, Unset):
            mapping = self.mapping.to_dict()

        filters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = []
            for filters_item_data in self.filters:
                filters_item = filters_item_data.to_dict()
                filters.append(filters_item)

        error_localizer = self.error_localizer

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        eval_group: None | str | Unset
        if isinstance(self.eval_group, Unset):
            eval_group = UNSET
        elif isinstance(self.eval_group, UUID):
            eval_group = str(self.eval_group)
        else:
            eval_group = self.eval_group

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if config is not UNSET:
            field_dict["config"] = config
        if mapping is not UNSET:
            field_dict["mapping"] = mapping
        if filters is not UNSET:
            field_dict["filters"] = filters
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if model is not UNSET:
            field_dict["model"] = model
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if eval_group is not UNSET:
            field_dict["eval_group"] = eval_group

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_definition_config import EvalConfigDefinitionConfig
        from ..models.eval_config_definition_filters_item import (
            EvalConfigDefinitionFiltersItem,
        )
        from ..models.eval_config_definition_mapping import EvalConfigDefinitionMapping

        d = dict(src_dict)
        template_id = UUID(d.pop("template_id"))

        name = d.pop("name", UNSET)

        _config = d.pop("config", UNSET)
        config: EvalConfigDefinitionConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalConfigDefinitionConfig.from_dict(_config)

        _mapping = d.pop("mapping", UNSET)
        mapping: EvalConfigDefinitionMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = EvalConfigDefinitionMapping.from_dict(_mapping)

        _filters = d.pop("filters", UNSET)
        filters: list[EvalConfigDefinitionFiltersItem] | Unset = UNSET
        if _filters is not UNSET:
            filters = []
            for filters_item_data in _filters:
                filters_item = EvalConfigDefinitionFiltersItem.from_dict(
                    filters_item_data
                )

                filters.append(filters_item)

        error_localizer = d.pop("error_localizer", UNSET)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

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

        def _parse_eval_group(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                eval_group_type_0 = UUID(data)

                return eval_group_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        eval_group = _parse_eval_group(d.pop("eval_group", UNSET))

        eval_config_definition = cls(
            template_id=template_id,
            name=name,
            config=config,
            mapping=mapping,
            filters=filters,
            error_localizer=error_localizer,
            model=model,
            kb_id=kb_id,
            eval_group=eval_group,
        )

        eval_config_definition.additional_properties = d
        return eval_config_definition

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
