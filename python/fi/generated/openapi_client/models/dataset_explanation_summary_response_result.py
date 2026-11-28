from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.dataset_explanation_summary_response_result_response import (
        DatasetExplanationSummaryResponseResultResponse,
    )


T = TypeVar("T", bound="DatasetExplanationSummaryResponseResult")


@_attrs_define
class DatasetExplanationSummaryResponseResult:
    """
    Attributes:
        response (DatasetExplanationSummaryResponseResultResponse):
        last_updated (datetime.datetime | None):
        status (str):
        row_count (int):
        min_rows_required (int):
    """

    response: DatasetExplanationSummaryResponseResultResponse
    last_updated: datetime.datetime | None
    status: str
    row_count: int
    min_rows_required: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        response = self.response.to_dict()

        last_updated: None | str
        if isinstance(self.last_updated, datetime.datetime):
            last_updated = self.last_updated.isoformat()
        else:
            last_updated = self.last_updated

        status = self.status

        row_count = self.row_count

        min_rows_required = self.min_rows_required

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "response": response,
                "last_updated": last_updated,
                "status": status,
                "row_count": row_count,
                "min_rows_required": min_rows_required,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_explanation_summary_response_result_response import (
            DatasetExplanationSummaryResponseResultResponse,
        )

        d = dict(src_dict)
        response = DatasetExplanationSummaryResponseResultResponse.from_dict(
            d.pop("response")
        )

        def _parse_last_updated(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_updated_type_0 = isoparse(data)

                return last_updated_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_updated = _parse_last_updated(d.pop("last_updated"))

        status = d.pop("status")

        row_count = d.pop("row_count")

        min_rows_required = d.pop("min_rows_required")

        dataset_explanation_summary_response_result = cls(
            response=response,
            last_updated=last_updated,
            status=status,
            row_count=row_count,
            min_rows_required=min_rows_required,
        )

        dataset_explanation_summary_response_result.additional_properties = d
        return dataset_explanation_summary_response_result

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
