from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_score_score_source import CreateScoreScoreSource
from ..models.create_score_source_type import CreateScoreSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_score_value import CreateScoreValue


T = TypeVar("T", bound="CreateScore")


@_attrs_define
class CreateScore:
    """
    Attributes:
        source_type (CreateScoreSourceType):
        source_id (str):
        label_id (UUID):
        value (CreateScoreValue):
        notes (str | Unset):  Default: ''.
        score_source (CreateScoreScoreSource | Unset):  Default: CreateScoreScoreSource.HUMAN.
        queue_item_id (None | Unset | UUID):
    """

    source_type: CreateScoreSourceType
    source_id: str
    label_id: UUID
    value: CreateScoreValue
    notes: str | Unset = ""
    score_source: CreateScoreScoreSource | Unset = CreateScoreScoreSource.HUMAN
    queue_item_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        source_id = self.source_id

        label_id = str(self.label_id)

        value = self.value.to_dict()

        notes = self.notes

        score_source: str | Unset = UNSET
        if not isinstance(self.score_source, Unset):
            score_source = self.score_source.value

        queue_item_id: None | str | Unset
        if isinstance(self.queue_item_id, Unset):
            queue_item_id = UNSET
        elif isinstance(self.queue_item_id, UUID):
            queue_item_id = str(self.queue_item_id)
        else:
            queue_item_id = self.queue_item_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_type": source_type,
                "source_id": source_id,
                "label_id": label_id,
                "value": value,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if score_source is not UNSET:
            field_dict["score_source"] = score_source
        if queue_item_id is not UNSET:
            field_dict["queue_item_id"] = queue_item_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_score_value import CreateScoreValue

        d = dict(src_dict)
        source_type = CreateScoreSourceType(d.pop("source_type"))

        source_id = d.pop("source_id")

        label_id = UUID(d.pop("label_id"))

        value = CreateScoreValue.from_dict(d.pop("value"))

        notes = d.pop("notes", UNSET)

        _score_source = d.pop("score_source", UNSET)
        score_source: CreateScoreScoreSource | Unset
        if isinstance(_score_source, Unset):
            score_source = UNSET
        else:
            score_source = CreateScoreScoreSource(_score_source)

        def _parse_queue_item_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                queue_item_id_type_0 = UUID(data)

                return queue_item_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        queue_item_id = _parse_queue_item_id(d.pop("queue_item_id", UNSET))

        create_score = cls(
            source_type=source_type,
            source_id=source_id,
            label_id=label_id,
            value=value,
            notes=notes,
            score_source=score_source,
            queue_item_id=queue_item_id,
        )

        create_score.additional_properties = d
        return create_score

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
