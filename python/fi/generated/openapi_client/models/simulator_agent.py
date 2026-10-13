from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SimulatorAgent")


@_attrs_define
class SimulatorAgent:
    """
    Attributes:
        name (str): Name of the simulator agent
        prompt (str): System prompt for the agent
        voice_provider (str): Voice service provider
        voice_name (str): Specific voice to use
        model (str): LLM model to use
        id (UUID | Unset):
        interrupt_sensitivity (float | Unset): Sensitivity for interruption detection (0-1)
        conversation_speed (float | Unset): Speed of conversation (0.1-3.0)
        finished_speaking_sensitivity (float | Unset): Sensitivity for detecting when speaker has finished (0-1)
        llm_temperature (float | Unset): Temperature setting for LLM (0-2)
        max_call_duration_in_minutes (int | Unset): Maximum call duration in minutes (1-180)
        initial_message_delay (int | Unset): Delay before initial message in seconds (0-60)
        initial_message (str | Unset): Initial message to send when conversation starts
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        organization (UUID | Unset): Organization this simulator agent belongs to
        deleted (bool | Unset):
        deleted_at (datetime.datetime | None | Unset):
        logo_url (str | Unset):
    """

    name: str
    prompt: str
    voice_provider: str
    voice_name: str
    model: str
    id: UUID | Unset = UNSET
    interrupt_sensitivity: float | Unset = UNSET
    conversation_speed: float | Unset = UNSET
    finished_speaking_sensitivity: float | Unset = UNSET
    llm_temperature: float | Unset = UNSET
    max_call_duration_in_minutes: int | Unset = UNSET
    initial_message_delay: int | Unset = UNSET
    initial_message: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    organization: UUID | Unset = UNSET
    deleted: bool | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    logo_url: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        prompt = self.prompt

        voice_provider = self.voice_provider

        voice_name = self.voice_name

        model = self.model

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        interrupt_sensitivity = self.interrupt_sensitivity

        conversation_speed = self.conversation_speed

        finished_speaking_sensitivity = self.finished_speaking_sensitivity

        llm_temperature = self.llm_temperature

        max_call_duration_in_minutes = self.max_call_duration_in_minutes

        initial_message_delay = self.initial_message_delay

        initial_message = self.initial_message

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        deleted = self.deleted

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        logo_url = self.logo_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "prompt": prompt,
                "voice_provider": voice_provider,
                "voice_name": voice_name,
                "model": model,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if interrupt_sensitivity is not UNSET:
            field_dict["interrupt_sensitivity"] = interrupt_sensitivity
        if conversation_speed is not UNSET:
            field_dict["conversation_speed"] = conversation_speed
        if finished_speaking_sensitivity is not UNSET:
            field_dict["finished_speaking_sensitivity"] = finished_speaking_sensitivity
        if llm_temperature is not UNSET:
            field_dict["llm_temperature"] = llm_temperature
        if max_call_duration_in_minutes is not UNSET:
            field_dict["max_call_duration_in_minutes"] = max_call_duration_in_minutes
        if initial_message_delay is not UNSET:
            field_dict["initial_message_delay"] = initial_message_delay
        if initial_message is not UNSET:
            field_dict["initial_message"] = initial_message
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if organization is not UNSET:
            field_dict["organization"] = organization
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if logo_url is not UNSET:
            field_dict["logo_url"] = logo_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        prompt = d.pop("prompt")

        voice_provider = d.pop("voice_provider")

        voice_name = d.pop("voice_name")

        model = d.pop("model")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        interrupt_sensitivity = d.pop("interrupt_sensitivity", UNSET)

        conversation_speed = d.pop("conversation_speed", UNSET)

        finished_speaking_sensitivity = d.pop("finished_speaking_sensitivity", UNSET)

        llm_temperature = d.pop("llm_temperature", UNSET)

        max_call_duration_in_minutes = d.pop("max_call_duration_in_minutes", UNSET)

        initial_message_delay = d.pop("initial_message_delay", UNSET)

        initial_message = d.pop("initial_message", UNSET)

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

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        deleted = d.pop("deleted", UNSET)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        logo_url = d.pop("logo_url", UNSET)

        simulator_agent = cls(
            name=name,
            prompt=prompt,
            voice_provider=voice_provider,
            voice_name=voice_name,
            model=model,
            id=id,
            interrupt_sensitivity=interrupt_sensitivity,
            conversation_speed=conversation_speed,
            finished_speaking_sensitivity=finished_speaking_sensitivity,
            llm_temperature=llm_temperature,
            max_call_duration_in_minutes=max_call_duration_in_minutes,
            initial_message_delay=initial_message_delay,
            initial_message=initial_message,
            created_at=created_at,
            updated_at=updated_at,
            organization=organization,
            deleted=deleted,
            deleted_at=deleted_at,
            logo_url=logo_url,
        )

        simulator_agent.additional_properties = d
        return simulator_agent

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
