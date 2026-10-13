from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PersonaFieldOptions")


@_attrs_define
class PersonaFieldOptions:
    """
    Attributes:
        gender_choices (str | Unset):
        age_group_choices (str | Unset):
        location_choices (str | Unset):
        profession_choices (str | Unset):
        personality_choices (str | Unset):
        communication_style_choices (str | Unset):
        accent_choices (str | Unset):
        language_choices (str | Unset):
        conversation_speed_choices (str | Unset):
        tone_choices (str | Unset):
        verbosity_choices (str | Unset):
        punctuation_choices (str | Unset):
        emoji_usage_choices (str | Unset):
        slang_usage_choices (str | Unset):
        typos_frequency_choices (str | Unset):
        regional_mix_choices (str | Unset):
    """

    gender_choices: str | Unset = UNSET
    age_group_choices: str | Unset = UNSET
    location_choices: str | Unset = UNSET
    profession_choices: str | Unset = UNSET
    personality_choices: str | Unset = UNSET
    communication_style_choices: str | Unset = UNSET
    accent_choices: str | Unset = UNSET
    language_choices: str | Unset = UNSET
    conversation_speed_choices: str | Unset = UNSET
    tone_choices: str | Unset = UNSET
    verbosity_choices: str | Unset = UNSET
    punctuation_choices: str | Unset = UNSET
    emoji_usage_choices: str | Unset = UNSET
    slang_usage_choices: str | Unset = UNSET
    typos_frequency_choices: str | Unset = UNSET
    regional_mix_choices: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        gender_choices = self.gender_choices

        age_group_choices = self.age_group_choices

        location_choices = self.location_choices

        profession_choices = self.profession_choices

        personality_choices = self.personality_choices

        communication_style_choices = self.communication_style_choices

        accent_choices = self.accent_choices

        language_choices = self.language_choices

        conversation_speed_choices = self.conversation_speed_choices

        tone_choices = self.tone_choices

        verbosity_choices = self.verbosity_choices

        punctuation_choices = self.punctuation_choices

        emoji_usage_choices = self.emoji_usage_choices

        slang_usage_choices = self.slang_usage_choices

        typos_frequency_choices = self.typos_frequency_choices

        regional_mix_choices = self.regional_mix_choices

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if gender_choices is not UNSET:
            field_dict["gender_choices"] = gender_choices
        if age_group_choices is not UNSET:
            field_dict["age_group_choices"] = age_group_choices
        if location_choices is not UNSET:
            field_dict["location_choices"] = location_choices
        if profession_choices is not UNSET:
            field_dict["profession_choices"] = profession_choices
        if personality_choices is not UNSET:
            field_dict["personality_choices"] = personality_choices
        if communication_style_choices is not UNSET:
            field_dict["communication_style_choices"] = communication_style_choices
        if accent_choices is not UNSET:
            field_dict["accent_choices"] = accent_choices
        if language_choices is not UNSET:
            field_dict["language_choices"] = language_choices
        if conversation_speed_choices is not UNSET:
            field_dict["conversation_speed_choices"] = conversation_speed_choices
        if tone_choices is not UNSET:
            field_dict["tone_choices"] = tone_choices
        if verbosity_choices is not UNSET:
            field_dict["verbosity_choices"] = verbosity_choices
        if punctuation_choices is not UNSET:
            field_dict["punctuation_choices"] = punctuation_choices
        if emoji_usage_choices is not UNSET:
            field_dict["emoji_usage_choices"] = emoji_usage_choices
        if slang_usage_choices is not UNSET:
            field_dict["slang_usage_choices"] = slang_usage_choices
        if typos_frequency_choices is not UNSET:
            field_dict["typos_frequency_choices"] = typos_frequency_choices
        if regional_mix_choices is not UNSET:
            field_dict["regional_mix_choices"] = regional_mix_choices

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        gender_choices = d.pop("gender_choices", UNSET)

        age_group_choices = d.pop("age_group_choices", UNSET)

        location_choices = d.pop("location_choices", UNSET)

        profession_choices = d.pop("profession_choices", UNSET)

        personality_choices = d.pop("personality_choices", UNSET)

        communication_style_choices = d.pop("communication_style_choices", UNSET)

        accent_choices = d.pop("accent_choices", UNSET)

        language_choices = d.pop("language_choices", UNSET)

        conversation_speed_choices = d.pop("conversation_speed_choices", UNSET)

        tone_choices = d.pop("tone_choices", UNSET)

        verbosity_choices = d.pop("verbosity_choices", UNSET)

        punctuation_choices = d.pop("punctuation_choices", UNSET)

        emoji_usage_choices = d.pop("emoji_usage_choices", UNSET)

        slang_usage_choices = d.pop("slang_usage_choices", UNSET)

        typos_frequency_choices = d.pop("typos_frequency_choices", UNSET)

        regional_mix_choices = d.pop("regional_mix_choices", UNSET)

        persona_field_options = cls(
            gender_choices=gender_choices,
            age_group_choices=age_group_choices,
            location_choices=location_choices,
            profession_choices=profession_choices,
            personality_choices=personality_choices,
            communication_style_choices=communication_style_choices,
            accent_choices=accent_choices,
            language_choices=language_choices,
            conversation_speed_choices=conversation_speed_choices,
            tone_choices=tone_choices,
            verbosity_choices=verbosity_choices,
            punctuation_choices=punctuation_choices,
            emoji_usage_choices=emoji_usage_choices,
            slang_usage_choices=slang_usage_choices,
            typos_frequency_choices=typos_frequency_choices,
            regional_mix_choices=regional_mix_choices,
        )

        persona_field_options.additional_properties = d
        return persona_field_options

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
