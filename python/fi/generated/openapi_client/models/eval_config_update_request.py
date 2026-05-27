from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_update_request_config import EvalConfigUpdateRequestConfig
    from ..models.eval_config_update_request_mapping import (
        EvalConfigUpdateRequestMapping,
    )


T = TypeVar("T", bound="EvalConfigUpdateRequest")


@_attrs_define
class EvalConfigUpdateRequest:
    """
    Attributes:
        config (EvalConfigUpdateRequestConfig | Unset): Updated evaluation configuration parameters.
        mapping (EvalConfigUpdateRequestMapping | Unset): Updated field mapping between test data and evaluation inputs.
        model (None | str | Unset): Model to use for evaluations.
        error_localizer (bool | Unset): Enable granular error localization in evaluation results.
        kb_id (None | Unset | UUID): UUID of a knowledge base to use for grounding. Pass null to clear.
        name (str | Unset): Updated name for the evaluation configuration.
        run (bool | Unset): When true, triggers an immediate rerun after updating. Defaults to false. Default: False.
        test_execution_id (None | Unset | UUID): UUID of the test execution to rerun against. Required when run is true.
    """

    config: EvalConfigUpdateRequestConfig | Unset = UNSET
    mapping: EvalConfigUpdateRequestMapping | Unset = UNSET
    model: None | str | Unset = UNSET
    error_localizer: bool | Unset = UNSET
    kb_id: None | Unset | UUID = UNSET
    name: str | Unset = UNSET
    run: bool | Unset = False
    test_execution_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mapping, Unset):
            mapping = self.mapping.to_dict()

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        error_localizer = self.error_localizer

        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        name = self.name

        run = self.run

        test_execution_id: None | str | Unset
        if isinstance(self.test_execution_id, Unset):
            test_execution_id = UNSET
        elif isinstance(self.test_execution_id, UUID):
            test_execution_id = str(self.test_execution_id)
        else:
            test_execution_id = self.test_execution_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if config is not UNSET:
            field_dict["config"] = config
        if mapping is not UNSET:
            field_dict["mapping"] = mapping
        if model is not UNSET:
            field_dict["model"] = model
        if error_localizer is not UNSET:
            field_dict["error_localizer"] = error_localizer
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if name is not UNSET:
            field_dict["name"] = name
        if run is not UNSET:
            field_dict["run"] = run
        if test_execution_id is not UNSET:
            field_dict["test_execution_id"] = test_execution_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_update_request_config import (
            EvalConfigUpdateRequestConfig,
        )
        from ..models.eval_config_update_request_mapping import (
            EvalConfigUpdateRequestMapping,
        )

        d = dict(src_dict)
        _config = d.pop("config", UNSET)
        config: EvalConfigUpdateRequestConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = EvalConfigUpdateRequestConfig.from_dict(_config)

        _mapping = d.pop("mapping", UNSET)
        mapping: EvalConfigUpdateRequestMapping | Unset
        if isinstance(_mapping, Unset):
            mapping = UNSET
        else:
            mapping = EvalConfigUpdateRequestMapping.from_dict(_mapping)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

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

        name = d.pop("name", UNSET)

        run = d.pop("run", UNSET)

        def _parse_test_execution_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                test_execution_id_type_0 = UUID(data)

                return test_execution_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        test_execution_id = _parse_test_execution_id(d.pop("test_execution_id", UNSET))

        eval_config_update_request = cls(
            config=config,
            mapping=mapping,
            model=model,
            error_localizer=error_localizer,
            kb_id=kb_id,
            name=name,
            run=run,
            test_execution_id=test_execution_id,
        )

        eval_config_update_request.additional_properties = d
        return eval_config_update_request

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
