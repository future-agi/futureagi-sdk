from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_selection_too_large_error_type import ApiSelectionTooLargeErrorType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_selection_too_large_detail import ApiSelectionTooLargeDetail


T = TypeVar("T", bound="ApiSelectionTooLargeError")


@_attrs_define
class ApiSelectionTooLargeError:
    """
    Attributes:
        message (str):
        error (ApiSelectionTooLargeDetail):
        status (bool | Unset):  Default: False.
        result (None | str | Unset):
        type_ (ApiSelectionTooLargeErrorType | Unset):
        code (str | Unset):  Default: 'selection_too_large'.
        detail (str | Unset):
    """

    message: str
    error: ApiSelectionTooLargeDetail
    status: bool | Unset = False
    result: None | str | Unset = UNSET
    type_: ApiSelectionTooLargeErrorType | Unset = UNSET
    code: str | Unset = "selection_too_large"
    detail: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        error = self.error.to_dict()

        status = self.status

        result: None | str | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        else:
            result = self.result

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        code = self.code

        detail = self.detail

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "error": error,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if result is not UNSET:
            field_dict["result"] = result
        if type_ is not UNSET:
            field_dict["type"] = type_
        if code is not UNSET:
            field_dict["code"] = code
        if detail is not UNSET:
            field_dict["detail"] = detail

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_selection_too_large_detail import ApiSelectionTooLargeDetail

        d = dict(src_dict)
        message = d.pop("message")

        error = ApiSelectionTooLargeDetail.from_dict(d.pop("error"))

        status = d.pop("status", UNSET)

        def _parse_result(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        _type_ = d.pop("type", UNSET)
        type_: ApiSelectionTooLargeErrorType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ApiSelectionTooLargeErrorType(_type_)

        code = d.pop("code", UNSET)

        detail = d.pop("detail", UNSET)

        api_selection_too_large_error = cls(
            message=message,
            error=error,
            status=status,
            result=result,
            type_=type_,
            code=code,
            detail=detail,
        )

        api_selection_too_large_error.additional_properties = d
        return api_selection_too_large_error

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
