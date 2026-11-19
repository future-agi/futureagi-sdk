from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateLinearIssueResult")


@_attrs_define
class CreateLinearIssueResult:
    """
    Attributes:
        already_linked (bool | Unset):
        issue_id (None | str | Unset):
        issue_url (None | str | Unset):
        issue_title (None | str | Unset):
    """

    already_linked: bool | Unset = UNSET
    issue_id: None | str | Unset = UNSET
    issue_url: None | str | Unset = UNSET
    issue_title: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        already_linked = self.already_linked

        issue_id: None | str | Unset
        if isinstance(self.issue_id, Unset):
            issue_id = UNSET
        else:
            issue_id = self.issue_id

        issue_url: None | str | Unset
        if isinstance(self.issue_url, Unset):
            issue_url = UNSET
        else:
            issue_url = self.issue_url

        issue_title: None | str | Unset
        if isinstance(self.issue_title, Unset):
            issue_title = UNSET
        else:
            issue_title = self.issue_title

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if already_linked is not UNSET:
            field_dict["already_linked"] = already_linked
        if issue_id is not UNSET:
            field_dict["issue_id"] = issue_id
        if issue_url is not UNSET:
            field_dict["issue_url"] = issue_url
        if issue_title is not UNSET:
            field_dict["issue_title"] = issue_title

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        already_linked = d.pop("already_linked", UNSET)

        def _parse_issue_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        issue_id = _parse_issue_id(d.pop("issue_id", UNSET))

        def _parse_issue_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        issue_url = _parse_issue_url(d.pop("issue_url", UNSET))

        def _parse_issue_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        issue_title = _parse_issue_title(d.pop("issue_title", UNSET))

        create_linear_issue_result = cls(
            already_linked=already_linked,
            issue_id=issue_id,
            issue_url=issue_url,
            issue_title=issue_title,
        )

        create_linear_issue_result.additional_properties = d
        return create_linear_issue_result

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
