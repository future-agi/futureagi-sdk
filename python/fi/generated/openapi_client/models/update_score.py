from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_score_score_source import UpdateScoreScoreSource
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_score_value import UpdateScoreValue


T = TypeVar("T", bound="UpdateScore")


@_attrs_define
class UpdateScore:
    """
    Attributes:
        value (UpdateScoreValue | Unset):
        notes (None | str | Unset):
        score_source (UpdateScoreScoreSource | Unset):
    """

    value: UpdateScoreValue | Unset = UNSET
    notes: None | str | Unset = UNSET
    score_source: UpdateScoreScoreSource | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value, Unset):
            value = self.value.to_dict()

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        score_source: str | Unset = UNSET
        if not isinstance(self.score_source, Unset):
            score_source = self.score_source.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if value is not UNSET:
            field_dict["value"] = value
        if notes is not UNSET:
            field_dict["notes"] = notes
        if score_source is not UNSET:
            field_dict["score_source"] = score_source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_score_value import UpdateScoreValue

        d = dict(src_dict)
        _value = d.pop("value", UNSET)
        value: UpdateScoreValue | Unset
        if isinstance(_value, Unset):
            value = UNSET
        else:
            value = UpdateScoreValue.from_dict(_value)

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        _score_source = d.pop("score_source", UNSET)
        score_source: UpdateScoreScoreSource | Unset
        if isinstance(_score_source, Unset):
            score_source = UNSET
        else:
            score_source = UpdateScoreScoreSource(_score_source)

        update_score = cls(
            value=value,
            notes=notes,
            score_source=score_source,
        )

        update_score.additional_properties = d
        return update_score

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
