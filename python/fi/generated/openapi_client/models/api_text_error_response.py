from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_text_error_response_type import ApiTextErrorResponseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_text_error_response_details import ApiTextErrorResponseDetails


T = TypeVar("T", bound="ApiTextErrorResponse")


@_attrs_define
class ApiTextErrorResponse:
    """
    Attributes:
        status (bool | Unset):  Default: False.
        type_ (ApiTextErrorResponseType | Unset):
        code (None | str | Unset):
        detail (None | str | Unset):
        result (None | str | Unset):
        message (None | str | Unset):
        error (None | str | Unset):
        attr (None | str | Unset):
        details (ApiTextErrorResponseDetails | Unset):
    """

    status: bool | Unset = False
    type_: ApiTextErrorResponseType | Unset = UNSET
    code: None | str | Unset = UNSET
    detail: None | str | Unset = UNSET
    result: None | str | Unset = UNSET
    message: None | str | Unset = UNSET
    error: None | str | Unset = UNSET
    attr: None | str | Unset = UNSET
    details: ApiTextErrorResponseDetails | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        detail: None | str | Unset
        if isinstance(self.detail, Unset):
            detail = UNSET
        else:
            detail = self.detail

        result: None | str | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        else:
            result = self.result

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        attr: None | str | Unset
        if isinstance(self.attr, Unset):
            attr = UNSET
        else:
            attr = self.attr

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if type_ is not UNSET:
            field_dict["type"] = type_
        if code is not UNSET:
            field_dict["code"] = code
        if detail is not UNSET:
            field_dict["detail"] = detail
        if result is not UNSET:
            field_dict["result"] = result
        if message is not UNSET:
            field_dict["message"] = message
        if error is not UNSET:
            field_dict["error"] = error
        if attr is not UNSET:
            field_dict["attr"] = attr
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_text_error_response_details import ApiTextErrorResponseDetails

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: ApiTextErrorResponseType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ApiTextErrorResponseType(_type_)

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        def _parse_detail(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        detail = _parse_detail(d.pop("detail", UNSET))

        def _parse_result(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_attr(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        attr = _parse_attr(d.pop("attr", UNSET))

        _details = d.pop("details", UNSET)
        details: ApiTextErrorResponseDetails | Unset
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = ApiTextErrorResponseDetails.from_dict(_details)

        api_text_error_response = cls(
            status=status,
            type_=type_,
            code=code,
            detail=detail,
            result=result,
            message=message,
            error=error,
            attr=attr,
            details=details,
        )

        api_text_error_response.additional_properties = d
        return api_text_error_response

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
