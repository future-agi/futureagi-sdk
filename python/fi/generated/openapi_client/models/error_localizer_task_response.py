from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_localizer_task_response_error_analysis import (
        ErrorLocalizerTaskResponseErrorAnalysis,
    )
    from ..models.error_localizer_task_response_eval_result import (
        ErrorLocalizerTaskResponseEvalResult,
    )
    from ..models.error_localizer_task_response_input_data import (
        ErrorLocalizerTaskResponseInputData,
    )
    from ..models.error_localizer_task_response_input_keys import (
        ErrorLocalizerTaskResponseInputKeys,
    )
    from ..models.error_localizer_task_response_input_types import (
        ErrorLocalizerTaskResponseInputTypes,
    )


T = TypeVar("T", bound="ErrorLocalizerTaskResponse")


@_attrs_define
class ErrorLocalizerTaskResponse:
    """
    Attributes:
        task_id (UUID | Unset):
        eval_config_id (None | str | Unset):
        status (str | Unset):
        eval_result (ErrorLocalizerTaskResponseEvalResult | Unset):
        eval_explanation (None | str | Unset):
        input_data (ErrorLocalizerTaskResponseInputData | Unset):
        input_keys (ErrorLocalizerTaskResponseInputKeys | Unset):
        input_types (ErrorLocalizerTaskResponseInputTypes | Unset):
        rule_prompt (None | str | Unset):
        error_analysis (ErrorLocalizerTaskResponseErrorAnalysis | Unset):
        selected_input_key (None | str | Unset):
        error_message (None | str | Unset):
        created_at (datetime.datetime | None | Unset):
        updated_at (datetime.datetime | None | Unset):
        eval_template_name (None | str | Unset):
        eval_template_id (None | Unset | UUID):
    """

    task_id: UUID | Unset = UNSET
    eval_config_id: None | str | Unset = UNSET
    status: str | Unset = UNSET
    eval_result: ErrorLocalizerTaskResponseEvalResult | Unset = UNSET
    eval_explanation: None | str | Unset = UNSET
    input_data: ErrorLocalizerTaskResponseInputData | Unset = UNSET
    input_keys: ErrorLocalizerTaskResponseInputKeys | Unset = UNSET
    input_types: ErrorLocalizerTaskResponseInputTypes | Unset = UNSET
    rule_prompt: None | str | Unset = UNSET
    error_analysis: ErrorLocalizerTaskResponseErrorAnalysis | Unset = UNSET
    selected_input_key: None | str | Unset = UNSET
    error_message: None | str | Unset = UNSET
    created_at: datetime.datetime | None | Unset = UNSET
    updated_at: datetime.datetime | None | Unset = UNSET
    eval_template_name: None | str | Unset = UNSET
    eval_template_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        task_id: str | Unset = UNSET
        if not isinstance(self.task_id, Unset):
            task_id = str(self.task_id)

        eval_config_id: None | str | Unset
        if isinstance(self.eval_config_id, Unset):
            eval_config_id = UNSET
        else:
            eval_config_id = self.eval_config_id

        status = self.status

        eval_result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_result, Unset):
            eval_result = self.eval_result.to_dict()

        eval_explanation: None | str | Unset
        if isinstance(self.eval_explanation, Unset):
            eval_explanation = UNSET
        else:
            eval_explanation = self.eval_explanation

        input_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_data, Unset):
            input_data = self.input_data.to_dict()

        input_keys: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_keys, Unset):
            input_keys = self.input_keys.to_dict()

        input_types: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_types, Unset):
            input_types = self.input_types.to_dict()

        rule_prompt: None | str | Unset
        if isinstance(self.rule_prompt, Unset):
            rule_prompt = UNSET
        else:
            rule_prompt = self.rule_prompt

        error_analysis: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error_analysis, Unset):
            error_analysis = self.error_analysis.to_dict()

        selected_input_key: None | str | Unset
        if isinstance(self.selected_input_key, Unset):
            selected_input_key = UNSET
        else:
            selected_input_key = self.selected_input_key

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        eval_template_name: None | str | Unset
        if isinstance(self.eval_template_name, Unset):
            eval_template_name = UNSET
        else:
            eval_template_name = self.eval_template_name

        eval_template_id: None | str | Unset
        if isinstance(self.eval_template_id, Unset):
            eval_template_id = UNSET
        elif isinstance(self.eval_template_id, UUID):
            eval_template_id = str(self.eval_template_id)
        else:
            eval_template_id = self.eval_template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if task_id is not UNSET:
            field_dict["task_id"] = task_id
        if eval_config_id is not UNSET:
            field_dict["eval_config_id"] = eval_config_id
        if status is not UNSET:
            field_dict["status"] = status
        if eval_result is not UNSET:
            field_dict["eval_result"] = eval_result
        if eval_explanation is not UNSET:
            field_dict["eval_explanation"] = eval_explanation
        if input_data is not UNSET:
            field_dict["input_data"] = input_data
        if input_keys is not UNSET:
            field_dict["input_keys"] = input_keys
        if input_types is not UNSET:
            field_dict["input_types"] = input_types
        if rule_prompt is not UNSET:
            field_dict["rule_prompt"] = rule_prompt
        if error_analysis is not UNSET:
            field_dict["error_analysis"] = error_analysis
        if selected_input_key is not UNSET:
            field_dict["selected_input_key"] = selected_input_key
        if error_message is not UNSET:
            field_dict["error_message"] = error_message
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if eval_template_name is not UNSET:
            field_dict["eval_template_name"] = eval_template_name
        if eval_template_id is not UNSET:
            field_dict["eval_template_id"] = eval_template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_localizer_task_response_error_analysis import (
            ErrorLocalizerTaskResponseErrorAnalysis,
        )
        from ..models.error_localizer_task_response_eval_result import (
            ErrorLocalizerTaskResponseEvalResult,
        )
        from ..models.error_localizer_task_response_input_data import (
            ErrorLocalizerTaskResponseInputData,
        )
        from ..models.error_localizer_task_response_input_keys import (
            ErrorLocalizerTaskResponseInputKeys,
        )
        from ..models.error_localizer_task_response_input_types import (
            ErrorLocalizerTaskResponseInputTypes,
        )

        d = dict(src_dict)
        _task_id = d.pop("task_id", UNSET)
        task_id: UUID | Unset
        if isinstance(_task_id, Unset):
            task_id = UNSET
        else:
            task_id = UUID(_task_id)

        def _parse_eval_config_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_config_id = _parse_eval_config_id(d.pop("eval_config_id", UNSET))

        status = d.pop("status", UNSET)

        _eval_result = d.pop("eval_result", UNSET)
        eval_result: ErrorLocalizerTaskResponseEvalResult | Unset
        if isinstance(_eval_result, Unset):
            eval_result = UNSET
        else:
            eval_result = ErrorLocalizerTaskResponseEvalResult.from_dict(_eval_result)

        def _parse_eval_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_explanation = _parse_eval_explanation(d.pop("eval_explanation", UNSET))

        _input_data = d.pop("input_data", UNSET)
        input_data: ErrorLocalizerTaskResponseInputData | Unset
        if isinstance(_input_data, Unset):
            input_data = UNSET
        else:
            input_data = ErrorLocalizerTaskResponseInputData.from_dict(_input_data)

        _input_keys = d.pop("input_keys", UNSET)
        input_keys: ErrorLocalizerTaskResponseInputKeys | Unset
        if isinstance(_input_keys, Unset):
            input_keys = UNSET
        else:
            input_keys = ErrorLocalizerTaskResponseInputKeys.from_dict(_input_keys)

        _input_types = d.pop("input_types", UNSET)
        input_types: ErrorLocalizerTaskResponseInputTypes | Unset
        if isinstance(_input_types, Unset):
            input_types = UNSET
        else:
            input_types = ErrorLocalizerTaskResponseInputTypes.from_dict(_input_types)

        def _parse_rule_prompt(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        rule_prompt = _parse_rule_prompt(d.pop("rule_prompt", UNSET))

        _error_analysis = d.pop("error_analysis", UNSET)
        error_analysis: ErrorLocalizerTaskResponseErrorAnalysis | Unset
        if isinstance(_error_analysis, Unset):
            error_analysis = UNSET
        else:
            error_analysis = ErrorLocalizerTaskResponseErrorAnalysis.from_dict(
                _error_analysis
            )

        def _parse_selected_input_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        selected_input_key = _parse_selected_input_key(
            d.pop("selected_input_key", UNSET)
        )

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        def _parse_created_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_eval_template_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_template_name = _parse_eval_template_name(
            d.pop("eval_template_name", UNSET)
        )

        def _parse_eval_template_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                eval_template_id_type_0 = UUID(data)

                return eval_template_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        eval_template_id = _parse_eval_template_id(d.pop("eval_template_id", UNSET))

        error_localizer_task_response = cls(
            task_id=task_id,
            eval_config_id=eval_config_id,
            status=status,
            eval_result=eval_result,
            eval_explanation=eval_explanation,
            input_data=input_data,
            input_keys=input_keys,
            input_types=input_types,
            rule_prompt=rule_prompt,
            error_analysis=error_analysis,
            selected_input_key=selected_input_key,
            error_message=error_message,
            created_at=created_at,
            updated_at=updated_at,
            eval_template_name=eval_template_name,
            eval_template_id=eval_template_id,
        )

        error_localizer_task_response.additional_properties = d
        return error_localizer_task_response

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
