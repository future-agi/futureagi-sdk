from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.selection_mode import SelectionMode
from ..models.selection_source_type import SelectionSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.selection_filter_item import SelectionFilterItem


T = TypeVar("T", bound="Selection")


@_attrs_define
class Selection:
    """
    Attributes:
        mode (SelectionMode):
        source_type (SelectionSourceType):
        project_id (UUID):
        filter_ (list[SelectionFilterItem] | Unset):
        exclude_ids (list[str] | Unset):
        remove_simulation_calls (bool | Unset):  Default: False.
        is_voice_call (bool | Unset):  Default: False.
    """

    mode: SelectionMode
    source_type: SelectionSourceType
    project_id: UUID
    filter_: list[SelectionFilterItem] | Unset = UNSET
    exclude_ids: list[str] | Unset = UNSET
    remove_simulation_calls: bool | Unset = False
    is_voice_call: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode = self.mode.value

        source_type = self.source_type.value

        project_id = str(self.project_id)

        filter_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = []
            for filter_item_data in self.filter_:
                filter_item = filter_item_data.to_dict()
                filter_.append(filter_item)

        exclude_ids: list[str] | Unset = UNSET
        if not isinstance(self.exclude_ids, Unset):
            exclude_ids = self.exclude_ids

        remove_simulation_calls = self.remove_simulation_calls

        is_voice_call = self.is_voice_call

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mode": mode,
                "source_type": source_type,
                "project_id": project_id,
            }
        )
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if exclude_ids is not UNSET:
            field_dict["exclude_ids"] = exclude_ids
        if remove_simulation_calls is not UNSET:
            field_dict["remove_simulation_calls"] = remove_simulation_calls
        if is_voice_call is not UNSET:
            field_dict["is_voice_call"] = is_voice_call

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.selection_filter_item import SelectionFilterItem

        d = dict(src_dict)
        mode = SelectionMode(d.pop("mode"))

        source_type = SelectionSourceType(d.pop("source_type"))

        project_id = UUID(d.pop("project_id"))

        _filter_ = d.pop("filter", UNSET)
        filter_: list[SelectionFilterItem] | Unset = UNSET
        if _filter_ is not UNSET:
            filter_ = []
            for filter_item_data in _filter_:
                filter_item = SelectionFilterItem.from_dict(filter_item_data)

                filter_.append(filter_item)

        exclude_ids = cast(list[str], d.pop("exclude_ids", UNSET))

        remove_simulation_calls = d.pop("remove_simulation_calls", UNSET)

        is_voice_call = d.pop("is_voice_call", UNSET)

        selection = cls(
            mode=mode,
            source_type=source_type,
            project_id=project_id,
            filter_=filter_,
            exclude_ids=exclude_ids,
            remove_simulation_calls=remove_simulation_calls,
            is_voice_call=is_voice_call,
        )

        selection.additional_properties = d
        return selection

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
