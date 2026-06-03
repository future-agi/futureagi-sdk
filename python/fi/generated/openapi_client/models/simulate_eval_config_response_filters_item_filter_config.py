from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="SimulateEvalConfigResponseFiltersItemFilterConfig")


@_attrs_define
class SimulateEvalConfigResponseFiltersItemFilterConfig:
    """
    Attributes:
        filter_type (str): Canonical field type, for example text, number, boolean, datetime, categorical, thumbs,
            annotator, or array.
        filter_op (str): Canonical operator from api_contracts/filter_contract.json, for example equals, not_equals, in,
            not_in, between, not_between, is_null, or is_not_null.
        filter_value (Any | Unset): Scalar, list, range tuple, boolean, or null depending on filter_op and filter_type.
        col_type (str | Unset): Column family such as SYSTEM_METRIC, SPAN_ATTRIBUTE, EVAL_METRIC, ANNOTATION, or NORMAL.
    """

    filter_type: str
    filter_op: str
    filter_value: Any | Unset = UNSET
    col_type: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        filter_type = self.filter_type

        filter_op = self.filter_op

        filter_value = self.filter_value

        col_type = self.col_type

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "filter_type": filter_type,
                "filter_op": filter_op,
            }
        )
        if filter_value is not UNSET:
            field_dict["filter_value"] = filter_value
        if col_type is not UNSET:
            field_dict["col_type"] = col_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        filter_type = d.pop("filter_type")

        filter_op = d.pop("filter_op")

        filter_value = d.pop("filter_value", UNSET)

        col_type = d.pop("col_type", UNSET)

        simulate_eval_config_response_filters_item_filter_config = cls(
            filter_type=filter_type,
            filter_op=filter_op,
            filter_value=filter_value,
            col_type=col_type,
        )

        return simulate_eval_config_response_filters_item_filter_config
