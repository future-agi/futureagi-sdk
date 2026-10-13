from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_transcript import CallTranscript


T = TypeVar("T", bound="TestExecutionTranscriptCall")


@_attrs_define
class TestExecutionTranscriptCall:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        phone_number (None | str | Unset):
        status (str | Unset):
        transcripts (list[CallTranscript] | Unset):
        total_transcripts (int | Unset):
        scenario_name (None | str | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    phone_number: None | str | Unset = UNSET
    status: str | Unset = UNSET
    transcripts: list[CallTranscript] | Unset = UNSET
    total_transcripts: int | Unset = UNSET
    scenario_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        phone_number: None | str | Unset
        if isinstance(self.phone_number, Unset):
            phone_number = UNSET
        else:
            phone_number = self.phone_number

        status = self.status

        transcripts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.transcripts, Unset):
            transcripts = []
            for transcripts_item_data in self.transcripts:
                transcripts_item = transcripts_item_data.to_dict()
                transcripts.append(transcripts_item)

        total_transcripts = self.total_transcripts

        scenario_name: None | str | Unset
        if isinstance(self.scenario_name, Unset):
            scenario_name = UNSET
        else:
            scenario_name = self.scenario_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number
        if status is not UNSET:
            field_dict["status"] = status
        if transcripts is not UNSET:
            field_dict["transcripts"] = transcripts
        if total_transcripts is not UNSET:
            field_dict["total_transcripts"] = total_transcripts
        if scenario_name is not UNSET:
            field_dict["scenario_name"] = scenario_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_transcript import CallTranscript

        d = dict(src_dict)
        _call_execution_id = d.pop("call_execution_id", UNSET)
        call_execution_id: UUID | Unset
        if isinstance(_call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = UUID(_call_execution_id)

        def _parse_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone_number = _parse_phone_number(d.pop("phone_number", UNSET))

        status = d.pop("status", UNSET)

        _transcripts = d.pop("transcripts", UNSET)
        transcripts: list[CallTranscript] | Unset = UNSET
        if _transcripts is not UNSET:
            transcripts = []
            for transcripts_item_data in _transcripts:
                transcripts_item = CallTranscript.from_dict(transcripts_item_data)

                transcripts.append(transcripts_item)

        total_transcripts = d.pop("total_transcripts", UNSET)

        def _parse_scenario_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scenario_name = _parse_scenario_name(d.pop("scenario_name", UNSET))

        test_execution_transcript_call = cls(
            call_execution_id=call_execution_id,
            phone_number=phone_number,
            status=status,
            transcripts=transcripts,
            total_transcripts=total_transcripts,
            scenario_name=scenario_name,
        )

        test_execution_transcript_call.additional_properties = d
        return test_execution_transcript_call

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
