from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HuggingFaceDatasetListItem")


@_attrs_define
class HuggingFaceDatasetListItem:
    """
    Attributes:
        id (str):
        name (str):
        downloads (int):
        likes (int):
        author (None | str | Unset):
    """

    id: str
    name: str
    downloads: int
    likes: int
    author: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        downloads = self.downloads

        likes = self.likes

        author: None | str | Unset
        if isinstance(self.author, Unset):
            author = UNSET
        else:
            author = self.author

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "downloads": downloads,
                "likes": likes,
            }
        )
        if author is not UNSET:
            field_dict["author"] = author

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        downloads = d.pop("downloads")

        likes = d.pop("likes")

        def _parse_author(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        author = _parse_author(d.pop("author", UNSET))

        hugging_face_dataset_list_item = cls(
            id=id,
            name=name,
            downloads=downloads,
            likes=likes,
            author=author,
        )

        hugging_face_dataset_list_item.additional_properties = d
        return hugging_face_dataset_list_item

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
