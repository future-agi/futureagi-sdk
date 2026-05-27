from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.optimiser_analysis_result_payload_response import (
        OptimiserAnalysisResultPayloadResponse,
    )


T = TypeVar("T", bound="OptimiserAnalysisResultPayload")


@_attrs_define
class OptimiserAnalysisResultPayload:
    """
    Attributes:
        response (OptimiserAnalysisResultPayloadResponse):
        status (str):
        last_updated (datetime.datetime | Unset):
        message (str | Unset):
    """

    response: OptimiserAnalysisResultPayloadResponse
    status: str
    last_updated: datetime.datetime | Unset = UNSET
    message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        response = self.response.to_dict()

        status = self.status

        last_updated: str | Unset = UNSET
        if not isinstance(self.last_updated, Unset):
            last_updated = self.last_updated.isoformat()

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "response": response,
                "status": status,
            }
        )
        if last_updated is not UNSET:
            field_dict["last_updated"] = last_updated
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.optimiser_analysis_result_payload_response import (
            OptimiserAnalysisResultPayloadResponse,
        )

        d = dict(src_dict)
        response = OptimiserAnalysisResultPayloadResponse.from_dict(d.pop("response"))

        status = d.pop("status")

        _last_updated = d.pop("last_updated", UNSET)
        last_updated: datetime.datetime | Unset
        if isinstance(_last_updated, Unset):
            last_updated = UNSET
        else:
            last_updated = isoparse(_last_updated)

        message = d.pop("message", UNSET)

        optimiser_analysis_result_payload = cls(
            response=response,
            status=status,
            last_updated=last_updated,
            message=message,
        )

        optimiser_analysis_result_payload.additional_properties = d
        return optimiser_analysis_result_payload

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
