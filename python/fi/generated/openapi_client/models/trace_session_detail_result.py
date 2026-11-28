from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_session_detail_result_response_item import (
        TraceSessionDetailResultResponseItem,
    )
    from ..models.trace_session_detail_result_session_metadata import (
        TraceSessionDetailResultSessionMetadata,
    )


T = TypeVar("T", bound="TraceSessionDetailResult")


@_attrs_define
class TraceSessionDetailResult:
    """
    Attributes:
        session_metadata (TraceSessionDetailResultSessionMetadata):
        response (list[TraceSessionDetailResultResponseItem]):
        next_ (bool):
    """

    session_metadata: TraceSessionDetailResultSessionMetadata
    response: list[TraceSessionDetailResultResponseItem]
    next_: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_metadata = self.session_metadata.to_dict()

        response = []
        for response_item_data in self.response:
            response_item = response_item_data.to_dict()
            response.append(response_item)

        next_ = self.next_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_metadata": session_metadata,
                "response": response,
                "next": next_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_session_detail_result_response_item import (
            TraceSessionDetailResultResponseItem,
        )
        from ..models.trace_session_detail_result_session_metadata import (
            TraceSessionDetailResultSessionMetadata,
        )

        d = dict(src_dict)
        session_metadata = TraceSessionDetailResultSessionMetadata.from_dict(
            d.pop("session_metadata")
        )

        response = []
        _response = d.pop("response")
        for response_item_data in _response:
            response_item = TraceSessionDetailResultResponseItem.from_dict(
                response_item_data
            )

            response.append(response_item)

        next_ = d.pop("next")

        trace_session_detail_result = cls(
            session_metadata=session_metadata,
            response=response,
            next_=next_,
        )

        trace_session_detail_result.additional_properties = d
        return trace_session_detail_result

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
