from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.call_transcript_speaker_role import CallTranscriptSpeakerRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="CallTranscript")


@_attrs_define
class CallTranscript:
    """
    Attributes:
        content (str): Transcript content
        id (UUID | Unset):
        speaker_role (CallTranscriptSpeakerRole | Unset): Role of the speaker (user or assistant)
        start_time_ms (int | Unset): Start time of this transcript segment in milliseconds
        start_time_seconds (str | Unset):
        end_time_ms (int | Unset): End time of this transcript segment in milliseconds
        end_time_seconds (str | Unset):
        confidence_score (float | Unset): Confidence score for this transcript segment
        created_at (datetime.datetime | Unset):
    """

    content: str
    id: UUID | Unset = UNSET
    speaker_role: CallTranscriptSpeakerRole | Unset = UNSET
    start_time_ms: int | Unset = UNSET
    start_time_seconds: str | Unset = UNSET
    end_time_ms: int | Unset = UNSET
    end_time_seconds: str | Unset = UNSET
    confidence_score: float | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        speaker_role: str | Unset = UNSET
        if not isinstance(self.speaker_role, Unset):
            speaker_role = self.speaker_role.value

        start_time_ms = self.start_time_ms

        start_time_seconds = self.start_time_seconds

        end_time_ms = self.end_time_ms

        end_time_seconds = self.end_time_seconds

        confidence_score = self.confidence_score

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if speaker_role is not UNSET:
            field_dict["speaker_role"] = speaker_role
        if start_time_ms is not UNSET:
            field_dict["start_time_ms"] = start_time_ms
        if start_time_seconds is not UNSET:
            field_dict["start_time_seconds"] = start_time_seconds
        if end_time_ms is not UNSET:
            field_dict["end_time_ms"] = end_time_ms
        if end_time_seconds is not UNSET:
            field_dict["end_time_seconds"] = end_time_seconds
        if confidence_score is not UNSET:
            field_dict["confidence_score"] = confidence_score
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content = d.pop("content")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _speaker_role = d.pop("speaker_role", UNSET)
        speaker_role: CallTranscriptSpeakerRole | Unset
        if isinstance(_speaker_role, Unset):
            speaker_role = UNSET
        else:
            speaker_role = CallTranscriptSpeakerRole(_speaker_role)

        start_time_ms = d.pop("start_time_ms", UNSET)

        start_time_seconds = d.pop("start_time_seconds", UNSET)

        end_time_ms = d.pop("end_time_ms", UNSET)

        end_time_seconds = d.pop("end_time_seconds", UNSET)

        confidence_score = d.pop("confidence_score", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        call_transcript = cls(
            content=content,
            id=id,
            speaker_role=speaker_role,
            start_time_ms=start_time_ms,
            start_time_seconds=start_time_seconds,
            end_time_ms=end_time_ms,
            end_time_seconds=end_time_seconds,
            confidence_score=confidence_score,
            created_at=created_at,
        )

        call_transcript.additional_properties = d
        return call_transcript

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
