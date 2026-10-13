from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.trace_session_graph_data_request_req_data_config_type import (
    TraceSessionGraphDataRequestReqDataConfigType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceSessionGraphDataRequestReqDataConfig")


@_attrs_define
class TraceSessionGraphDataRequestReqDataConfig:
    """
    Attributes:
        id (str):
        type_ (TraceSessionGraphDataRequestReqDataConfigType):
        output_type (str | Unset):
        eval_output_type (str | Unset):
        choices (list[str] | Unset):
        value (Any | Unset):
        filter_op (str | Unset):
        filter_value (Any | Unset):
    """

    id: str
    type_: TraceSessionGraphDataRequestReqDataConfigType
    output_type: str | Unset = UNSET
    eval_output_type: str | Unset = UNSET
    choices: list[str] | Unset = UNSET
    value: Any | Unset = UNSET
    filter_op: str | Unset = UNSET
    filter_value: Any | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_.value

        output_type = self.output_type

        eval_output_type = self.eval_output_type

        choices: list[str] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = self.choices

        value = self.value

        filter_op = self.filter_op

        filter_value = self.filter_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if eval_output_type is not UNSET:
            field_dict["eval_output_type"] = eval_output_type
        if choices is not UNSET:
            field_dict["choices"] = choices
        if value is not UNSET:
            field_dict["value"] = value
        if filter_op is not UNSET:
            field_dict["filter_op"] = filter_op
        if filter_value is not UNSET:
            field_dict["filter_value"] = filter_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        type_ = TraceSessionGraphDataRequestReqDataConfigType(d.pop("type"))

        output_type = d.pop("output_type", UNSET)

        eval_output_type = d.pop("eval_output_type", UNSET)

        choices = cast(list[str], d.pop("choices", UNSET))

        value = d.pop("value", UNSET)

        filter_op = d.pop("filter_op", UNSET)

        filter_value = d.pop("filter_value", UNSET)

        trace_session_graph_data_request_req_data_config = cls(
            id=id,
            type_=type_,
            output_type=output_type,
            eval_output_type=eval_output_type,
            choices=choices,
            value=value,
            filter_op=filter_op,
            filter_value=filter_value,
        )

        return trace_session_graph_data_request_req_data_config
