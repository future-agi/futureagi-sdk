from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.score_score_source import ScoreScoreSource
from ..models.score_source_type import ScoreSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.score_label_settings import ScoreLabelSettings
    from ..models.score_value import ScoreValue


T = TypeVar("T", bound="Score")


@_attrs_define
class Score:
    """
    Attributes:
        source_type (ScoreSourceType):
        value (ScoreValue):
        id (UUID | Unset):
        source_id (str | Unset):
        label_id (UUID | Unset):
        label_name (str | Unset):
        label_type (str | Unset):
        label_settings (ScoreLabelSettings | Unset):
        label_allow_notes (bool | Unset):
        score_source (ScoreScoreSource | Unset):
        notes (None | str | Unset):
        annotator (None | Unset | UUID):
        annotator_name (str | Unset):
        annotator_email (str | Unset):
        queue_item (None | Unset | UUID):
        queue_id (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
    """

    source_type: ScoreSourceType
    value: ScoreValue
    id: UUID | Unset = UNSET
    source_id: str | Unset = UNSET
    label_id: UUID | Unset = UNSET
    label_name: str | Unset = UNSET
    label_type: str | Unset = UNSET
    label_settings: ScoreLabelSettings | Unset = UNSET
    label_allow_notes: bool | Unset = UNSET
    score_source: ScoreScoreSource | Unset = UNSET
    notes: None | str | Unset = UNSET
    annotator: None | Unset | UUID = UNSET
    annotator_name: str | Unset = UNSET
    annotator_email: str | Unset = UNSET
    queue_item: None | Unset | UUID = UNSET
    queue_id: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        value = self.value.to_dict()

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        source_id = self.source_id

        label_id: str | Unset = UNSET
        if not isinstance(self.label_id, Unset):
            label_id = str(self.label_id)

        label_name = self.label_name

        label_type = self.label_type

        label_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.label_settings, Unset):
            label_settings = self.label_settings.to_dict()

        label_allow_notes = self.label_allow_notes

        score_source: str | Unset = UNSET
        if not isinstance(self.score_source, Unset):
            score_source = self.score_source.value

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        annotator: None | str | Unset
        if isinstance(self.annotator, Unset):
            annotator = UNSET
        elif isinstance(self.annotator, UUID):
            annotator = str(self.annotator)
        else:
            annotator = self.annotator

        annotator_name = self.annotator_name

        annotator_email = self.annotator_email

        queue_item: None | str | Unset
        if isinstance(self.queue_item, Unset):
            queue_item = UNSET
        elif isinstance(self.queue_item, UUID):
            queue_item = str(self.queue_item)
        else:
            queue_item = self.queue_item

        queue_id = self.queue_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_type": source_type,
                "value": value,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if source_id is not UNSET:
            field_dict["source_id"] = source_id
        if label_id is not UNSET:
            field_dict["label_id"] = label_id
        if label_name is not UNSET:
            field_dict["label_name"] = label_name
        if label_type is not UNSET:
            field_dict["label_type"] = label_type
        if label_settings is not UNSET:
            field_dict["label_settings"] = label_settings
        if label_allow_notes is not UNSET:
            field_dict["label_allow_notes"] = label_allow_notes
        if score_source is not UNSET:
            field_dict["score_source"] = score_source
        if notes is not UNSET:
            field_dict["notes"] = notes
        if annotator is not UNSET:
            field_dict["annotator"] = annotator
        if annotator_name is not UNSET:
            field_dict["annotator_name"] = annotator_name
        if annotator_email is not UNSET:
            field_dict["annotator_email"] = annotator_email
        if queue_item is not UNSET:
            field_dict["queue_item"] = queue_item
        if queue_id is not UNSET:
            field_dict["queue_id"] = queue_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.score_label_settings import ScoreLabelSettings
        from ..models.score_value import ScoreValue

        d = dict(src_dict)
        source_type = ScoreSourceType(d.pop("source_type"))

        value = ScoreValue.from_dict(d.pop("value"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        source_id = d.pop("source_id", UNSET)

        _label_id = d.pop("label_id", UNSET)
        label_id: UUID | Unset
        if isinstance(_label_id, Unset):
            label_id = UNSET
        else:
            label_id = UUID(_label_id)

        label_name = d.pop("label_name", UNSET)

        label_type = d.pop("label_type", UNSET)

        _label_settings = d.pop("label_settings", UNSET)
        label_settings: ScoreLabelSettings | Unset
        if isinstance(_label_settings, Unset):
            label_settings = UNSET
        else:
            label_settings = ScoreLabelSettings.from_dict(_label_settings)

        label_allow_notes = d.pop("label_allow_notes", UNSET)

        _score_source = d.pop("score_source", UNSET)
        score_source: ScoreScoreSource | Unset
        if isinstance(_score_source, Unset):
            score_source = UNSET
        else:
            score_source = ScoreScoreSource(_score_source)

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_annotator(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                annotator_type_0 = UUID(data)

                return annotator_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        annotator = _parse_annotator(d.pop("annotator", UNSET))

        annotator_name = d.pop("annotator_name", UNSET)

        annotator_email = d.pop("annotator_email", UNSET)

        def _parse_queue_item(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                queue_item_type_0 = UUID(data)

                return queue_item_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        queue_item = _parse_queue_item(d.pop("queue_item", UNSET))

        queue_id = d.pop("queue_id", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        score = cls(
            source_type=source_type,
            value=value,
            id=id,
            source_id=source_id,
            label_id=label_id,
            label_name=label_name,
            label_type=label_type,
            label_settings=label_settings,
            label_allow_notes=label_allow_notes,
            score_source=score_source,
            notes=notes,
            annotator=annotator,
            annotator_name=annotator_name,
            annotator_email=annotator_email,
            queue_item=queue_item,
            queue_id=queue_id,
            created_at=created_at,
            updated_at=updated_at,
        )

        score.additional_properties = d
        return score

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
