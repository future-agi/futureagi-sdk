from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.simulate_eval_config_response_config import (
        SimulateEvalConfigResponseConfig,
    )
    from ..models.simulate_eval_config_response_filters_item import (
        SimulateEvalConfigResponseFiltersItem,
    )
    from ..models.simulate_eval_config_response_mapping import (
        SimulateEvalConfigResponseMapping,
    )


T = TypeVar("T", bound="SimulateEvalConfigResponse")


@_attrs_define
class SimulateEvalConfigResponse:
    """
    Attributes:
        id (UUID | Unset):
        name (None | str | Unset):
        config (SimulateEvalConfigResponseConfig | Unset):
        mapping (SimulateEvalConfigResponseMapping | Unset):
        filters (list[SimulateEvalConfigResponseFiltersItem] | Unset):
        error_localizer (bool | Unset):
        model (None | str | Unset):
        status (None | str | Unset):
        eval_group (None | str | Unset):
        template_id (None | Unset | UUID):
    """

    id: UUID | Unset = UNSET
    name: None | str | Unset = UNSET
    config: SimulateEvalConfigResponseConfig | Unset = UNSET
    mapping: SimulateEvalConfigResponseMapping | Unset = UNSET
    filters: list[SimulateEvalConfigResponseFiltersItem] | Unset = UNSET
    error_localizer: bool | Unset = UNSET
    model: None | str | Unset = UNSET
    status: None | str | Unset = UNSET
    eval_group: None | str | Unset = UNSET
    template_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
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

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        eval_group: None | str | Unset
        if isinstance(self.eval_group, Unset):
            eval_group = UNSET
        else:
            eval_group = self.eval_group

        template_id: None | str | Unset
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        elif isinstance(self.template_id, UUID):
            template_id = str(self.template_id)
        else:
            template_id = self.template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
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
        if status is not UNSET:
            field_dict["status"] = status
        if eval_group is not UNSET:
            field_dict["eval_group"] = eval_group
        if template_id is not UNSET:
            field_dict["template_id"] = template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulate_eval_config_response_config import (
            SimulateEvalConfigResponseConfig,
        )
        from ..models.simulate_eval_config_response_filters_item import (
            SimulateEvalConfigResponseFiltersItem,
        )
        from ..models.simulate_eval_config_response_mapping import (
            SimulateEvalConfigResponseMapping,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        _config = d.pop("config", UNSET)
        config: SimulateEvalConfigResponseConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = SimulateEvalConfigResponseConfig.from_dict(_config)

        _mapping = d.pop("mapping", UNSET)
        mapping: SimulateEvalConfigResponseMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = SimulateEvalConfigResponseMapping.from_dict(_mapping)

        _filters = d.pop("filters", UNSET)
        filters: list[SimulateEvalConfigResponseFiltersItem] | Unset = UNSET
        if _filters is not UNSET:
            filters = []
            for filters_item_data in _filters:
                filters_item = SimulateEvalConfigResponseFiltersItem.from_dict(
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

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_eval_group(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_group = _parse_eval_group(d.pop("eval_group", UNSET))

        def _parse_template_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                template_id_type_0 = UUID(data)

                return template_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        template_id = _parse_template_id(d.pop("template_id", UNSET))

        simulate_eval_config_response = cls(
            id=id,
            name=name,
            config=config,
            mapping=mapping,
            filters=filters,
            error_localizer=error_localizer,
            model=model,
            status=status,
            eval_group=eval_group,
            template_id=template_id,
        )

        simulate_eval_config_response.additional_properties = d
        return simulate_eval_config_response

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
