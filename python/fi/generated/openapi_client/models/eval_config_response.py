from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_config_response_model import EvalConfigResponseModel
from ..models.eval_config_response_status import EvalConfigResponseStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_response_config import EvalConfigResponseConfig
    from ..models.eval_config_response_filters import EvalConfigResponseFilters
    from ..models.eval_config_response_mapping import EvalConfigResponseMapping


T = TypeVar("T", bound="EvalConfigResponse")


@_attrs_define
class EvalConfigResponse:
    """
    Attributes:
        id (UUID | Unset):
        name (None | str | Unset):
        config (EvalConfigResponseConfig | Unset):
        mapping (EvalConfigResponseMapping | Unset):
        filters (EvalConfigResponseFilters | Unset):
        error_localizer (bool | Unset):
        model (EvalConfigResponseModel | Unset):
        status (EvalConfigResponseStatus | Unset):
        eval_group (str | Unset):
        template_id (UUID | Unset):
    """

    id: UUID | Unset = UNSET
    name: None | str | Unset = UNSET
    config: EvalConfigResponseConfig | Unset = UNSET
    mapping: EvalConfigResponseMapping | Unset = UNSET
    filters: EvalConfigResponseFilters | Unset = UNSET
    error_localizer: bool | Unset = UNSET
    model: EvalConfigResponseModel | Unset = UNSET
    status: EvalConfigResponseStatus | Unset = UNSET
    eval_group: str | Unset = UNSET
    template_id: UUID | Unset = UNSET
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

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        error_localizer = self.error_localizer

        model: str | Unset = UNSET
        if not isinstance(self.model, Unset):
            model = self.model.value

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        eval_group = self.eval_group

        template_id: str | Unset = UNSET
        if not isinstance(self.template_id, Unset):
            template_id = str(self.template_id)

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
        from ..models.eval_config_response_config import EvalConfigResponseConfig
        from ..models.eval_config_response_filters import EvalConfigResponseFilters
        from ..models.eval_config_response_mapping import EvalConfigResponseMapping

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
        config: EvalConfigResponseConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalConfigResponseConfig.from_dict(_config)

        _mapping = d.pop("mapping", UNSET)
        mapping: EvalConfigResponseMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = EvalConfigResponseMapping.from_dict(_mapping)

        _filters = d.pop("filters", UNSET)
        filters: EvalConfigResponseFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = EvalConfigResponseFilters.from_dict(_filters)

        error_localizer = d.pop("error_localizer", UNSET)

        _model = d.pop("model", UNSET)
        model: EvalConfigResponseModel | Unset
        if isinstance(_model, Unset):
            model = UNSET
        else:
            model = EvalConfigResponseModel(_model)

        _status = d.pop("status", UNSET)
        status: EvalConfigResponseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = EvalConfigResponseStatus(_status)

        eval_group = d.pop("eval_group", UNSET)

        _template_id = d.pop("template_id", UNSET)
        template_id: UUID | Unset
        if isinstance(_template_id, Unset):
            template_id = UNSET
        else:
            template_id = UUID(_template_id)

        eval_config_response = cls(
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

        eval_config_response.additional_properties = d
        return eval_config_response

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
