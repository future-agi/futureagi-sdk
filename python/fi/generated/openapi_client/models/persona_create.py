from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.persona_create_custom_properties import PersonaCreateCustomProperties


T = TypeVar("T", bound="PersonaCreate")


@_attrs_define
class PersonaCreate:
    """
    Attributes:
        name (str):
        description (str):
        gender (list[str] | None | Unset):
        age_group (list[str] | None | Unset):
        location (list[str] | None | Unset):
        profession (list[str] | None | Unset):
        personality (list[str] | None | Unset):
        communication_style (list[str] | None | Unset):
        accent (list[str] | None | Unset):
        multilingual (bool | Unset):  Default: False.
        language (list[str] | None | Unset):
        conversation_speed (list[str] | None | Unset):
        background_sound (bool | None | Unset):
        finished_speaking_sensitivity (list[str] | None | Unset):
        interrupt_sensitivity (list[str] | None | Unset):
        keywords (list[str] | None | Unset):
        custom_properties (PersonaCreateCustomProperties | Unset):
        additional_instruction (None | str | Unset):  Default: ''.
        simulation_type (None | str | Unset):  Default: 'voice'.
        tone (None | str | Unset):  Default: 'casual'.
        punctuation (None | str | Unset):  Default: 'clean'.
        slang_usage (None | str | Unset):  Default: 'light'.
        typos_frequency (None | str | Unset):  Default: 'rare'.
        regional_mix (None | str | Unset):  Default: 'light'.
        emoji_usage (None | str | Unset):  Default: 'light'.
        verbosity (None | str | Unset):  Default: 'balanced'.
    """

    name: str
    description: str
    gender: list[str] | None | Unset = UNSET
    age_group: list[str] | None | Unset = UNSET
    location: list[str] | None | Unset = UNSET
    profession: list[str] | None | Unset = UNSET
    personality: list[str] | None | Unset = UNSET
    communication_style: list[str] | None | Unset = UNSET
    accent: list[str] | None | Unset = UNSET
    multilingual: bool | Unset = False
    language: list[str] | None | Unset = UNSET
    conversation_speed: list[str] | None | Unset = UNSET
    background_sound: bool | None | Unset = UNSET
    finished_speaking_sensitivity: list[str] | None | Unset = UNSET
    interrupt_sensitivity: list[str] | None | Unset = UNSET
    keywords: list[str] | None | Unset = UNSET
    custom_properties: PersonaCreateCustomProperties | Unset = UNSET
    additional_instruction: None | str | Unset = ""
    simulation_type: None | str | Unset = "voice"
    tone: None | str | Unset = "casual"
    punctuation: None | str | Unset = "clean"
    slang_usage: None | str | Unset = "light"
    typos_frequency: None | str | Unset = "rare"
    regional_mix: None | str | Unset = "light"
    emoji_usage: None | str | Unset = "light"
    verbosity: None | str | Unset = "balanced"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        gender: list[str] | None | Unset
        if isinstance(self.gender, Unset):
            gender = UNSET
        elif isinstance(self.gender, list):
            gender = self.gender

        else:
            gender = self.gender

        age_group: list[str] | None | Unset
        if isinstance(self.age_group, Unset):
            age_group = UNSET
        elif isinstance(self.age_group, list):
            age_group = self.age_group

        else:
            age_group = self.age_group

        location: list[str] | None | Unset
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, list):
            location = self.location

        else:
            location = self.location

        profession: list[str] | None | Unset
        if isinstance(self.profession, Unset):
            profession = UNSET
        elif isinstance(self.profession, list):
            profession = self.profession

        else:
            profession = self.profession

        personality: list[str] | None | Unset
        if isinstance(self.personality, Unset):
            personality = UNSET
        elif isinstance(self.personality, list):
            personality = self.personality

        else:
            personality = self.personality

        communication_style: list[str] | None | Unset
        if isinstance(self.communication_style, Unset):
            communication_style = UNSET
        elif isinstance(self.communication_style, list):
            communication_style = self.communication_style

        else:
            communication_style = self.communication_style

        accent: list[str] | None | Unset
        if isinstance(self.accent, Unset):
            accent = UNSET
        elif isinstance(self.accent, list):
            accent = self.accent

        else:
            accent = self.accent

        multilingual = self.multilingual

        language: list[str] | None | Unset
        if isinstance(self.language, Unset):
            language = UNSET
        elif isinstance(self.language, list):
            language = self.language

        else:
            language = self.language

        conversation_speed: list[str] | None | Unset
        if isinstance(self.conversation_speed, Unset):
            conversation_speed = UNSET
        elif isinstance(self.conversation_speed, list):
            conversation_speed = self.conversation_speed

        else:
            conversation_speed = self.conversation_speed

        background_sound: bool | None | Unset
        if isinstance(self.background_sound, Unset):
            background_sound = UNSET
        else:
            background_sound = self.background_sound

        finished_speaking_sensitivity: list[str] | None | Unset
        if isinstance(self.finished_speaking_sensitivity, Unset):
            finished_speaking_sensitivity = UNSET
        elif isinstance(self.finished_speaking_sensitivity, list):
            finished_speaking_sensitivity = self.finished_speaking_sensitivity

        else:
            finished_speaking_sensitivity = self.finished_speaking_sensitivity

        interrupt_sensitivity: list[str] | None | Unset
        if isinstance(self.interrupt_sensitivity, Unset):
            interrupt_sensitivity = UNSET
        elif isinstance(self.interrupt_sensitivity, list):
            interrupt_sensitivity = self.interrupt_sensitivity

        else:
            interrupt_sensitivity = self.interrupt_sensitivity

        keywords: list[str] | None | Unset
        if isinstance(self.keywords, Unset):
            keywords = UNSET
        elif isinstance(self.keywords, list):
            keywords = self.keywords

        else:
            keywords = self.keywords

        custom_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_properties, Unset):
            custom_properties = self.custom_properties.to_dict()

        additional_instruction: None | str | Unset
        if isinstance(self.additional_instruction, Unset):
            additional_instruction = UNSET
        else:
            additional_instruction = self.additional_instruction

        simulation_type: None | str | Unset
        if isinstance(self.simulation_type, Unset):
            simulation_type = UNSET
        else:
            simulation_type = self.simulation_type

        tone: None | str | Unset
        if isinstance(self.tone, Unset):
            tone = UNSET
        else:
            tone = self.tone

        punctuation: None | str | Unset
        if isinstance(self.punctuation, Unset):
            punctuation = UNSET
        else:
            punctuation = self.punctuation

        slang_usage: None | str | Unset
        if isinstance(self.slang_usage, Unset):
            slang_usage = UNSET
        else:
            slang_usage = self.slang_usage

        typos_frequency: None | str | Unset
        if isinstance(self.typos_frequency, Unset):
            typos_frequency = UNSET
        else:
            typos_frequency = self.typos_frequency

        regional_mix: None | str | Unset
        if isinstance(self.regional_mix, Unset):
            regional_mix = UNSET
        else:
            regional_mix = self.regional_mix

        emoji_usage: None | str | Unset
        if isinstance(self.emoji_usage, Unset):
            emoji_usage = UNSET
        else:
            emoji_usage = self.emoji_usage

        verbosity: None | str | Unset
        if isinstance(self.verbosity, Unset):
            verbosity = UNSET
        else:
            verbosity = self.verbosity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
            }
        )
        if gender is not UNSET:
            field_dict["gender"] = gender
        if age_group is not UNSET:
            field_dict["age_group"] = age_group
        if location is not UNSET:
            field_dict["location"] = location
        if profession is not UNSET:
            field_dict["profession"] = profession
        if personality is not UNSET:
            field_dict["personality"] = personality
        if communication_style is not UNSET:
            field_dict["communication_style"] = communication_style
        if accent is not UNSET:
            field_dict["accent"] = accent
        if multilingual is not UNSET:
            field_dict["multilingual"] = multilingual
        if language is not UNSET:
            field_dict["language"] = language
        if conversation_speed is not UNSET:
            field_dict["conversation_speed"] = conversation_speed
        if background_sound is not UNSET:
            field_dict["background_sound"] = background_sound
        if finished_speaking_sensitivity is not UNSET:
            field_dict["finished_speaking_sensitivity"] = finished_speaking_sensitivity
        if interrupt_sensitivity is not UNSET:
            field_dict["interrupt_sensitivity"] = interrupt_sensitivity
        if keywords is not UNSET:
            field_dict["keywords"] = keywords
        if custom_properties is not UNSET:
            field_dict["custom_properties"] = custom_properties
        if additional_instruction is not UNSET:
            field_dict["additional_instruction"] = additional_instruction
        if simulation_type is not UNSET:
            field_dict["simulation_type"] = simulation_type
        if tone is not UNSET:
            field_dict["tone"] = tone
        if punctuation is not UNSET:
            field_dict["punctuation"] = punctuation
        if slang_usage is not UNSET:
            field_dict["slang_usage"] = slang_usage
        if typos_frequency is not UNSET:
            field_dict["typos_frequency"] = typos_frequency
        if regional_mix is not UNSET:
            field_dict["regional_mix"] = regional_mix
        if emoji_usage is not UNSET:
            field_dict["emoji_usage"] = emoji_usage
        if verbosity is not UNSET:
            field_dict["verbosity"] = verbosity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.persona_create_custom_properties import (
            PersonaCreateCustomProperties,
        )

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        def _parse_gender(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                gender_type_0 = cast(list[str], data)

                return gender_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        gender = _parse_gender(d.pop("gender", UNSET))

        def _parse_age_group(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                age_group_type_0 = cast(list[str], data)

                return age_group_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        age_group = _parse_age_group(d.pop("age_group", UNSET))

        def _parse_location(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                location_type_0 = cast(list[str], data)

                return location_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        location = _parse_location(d.pop("location", UNSET))

        def _parse_profession(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                profession_type_0 = cast(list[str], data)

                return profession_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        profession = _parse_profession(d.pop("profession", UNSET))

        def _parse_personality(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                personality_type_0 = cast(list[str], data)

                return personality_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        personality = _parse_personality(d.pop("personality", UNSET))

        def _parse_communication_style(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_style_type_0 = cast(list[str], data)

                return communication_style_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        communication_style = _parse_communication_style(
            d.pop("communication_style", UNSET)
        )

        def _parse_accent(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                accent_type_0 = cast(list[str], data)

                return accent_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        accent = _parse_accent(d.pop("accent", UNSET))

        multilingual = d.pop("multilingual", UNSET)

        def _parse_language(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                language_type_0 = cast(list[str], data)

                return language_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        language = _parse_language(d.pop("language", UNSET))

        def _parse_conversation_speed(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                conversation_speed_type_0 = cast(list[str], data)

                return conversation_speed_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        conversation_speed = _parse_conversation_speed(
            d.pop("conversation_speed", UNSET)
        )

        def _parse_background_sound(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        background_sound = _parse_background_sound(d.pop("background_sound", UNSET))

        def _parse_finished_speaking_sensitivity(
            data: object,
        ) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                finished_speaking_sensitivity_type_0 = cast(list[str], data)

                return finished_speaking_sensitivity_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        finished_speaking_sensitivity = _parse_finished_speaking_sensitivity(
            d.pop("finished_speaking_sensitivity", UNSET)
        )

        def _parse_interrupt_sensitivity(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                interrupt_sensitivity_type_0 = cast(list[str], data)

                return interrupt_sensitivity_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        interrupt_sensitivity = _parse_interrupt_sensitivity(
            d.pop("interrupt_sensitivity", UNSET)
        )

        def _parse_keywords(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                keywords_type_0 = cast(list[str], data)

                return keywords_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        keywords = _parse_keywords(d.pop("keywords", UNSET))

        _custom_properties = d.pop("custom_properties", UNSET)
        custom_properties: PersonaCreateCustomProperties | Unset
        if isinstance(_custom_properties, Unset):
            custom_properties = UNSET
        else:
            custom_properties = PersonaCreateCustomProperties.from_dict(
                _custom_properties
            )

        def _parse_additional_instruction(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_instruction = _parse_additional_instruction(
            d.pop("additional_instruction", UNSET)
        )

        def _parse_simulation_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        simulation_type = _parse_simulation_type(d.pop("simulation_type", UNSET))

        def _parse_tone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tone = _parse_tone(d.pop("tone", UNSET))

        def _parse_punctuation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        punctuation = _parse_punctuation(d.pop("punctuation", UNSET))

        def _parse_slang_usage(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        slang_usage = _parse_slang_usage(d.pop("slang_usage", UNSET))

        def _parse_typos_frequency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        typos_frequency = _parse_typos_frequency(d.pop("typos_frequency", UNSET))

        def _parse_regional_mix(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        regional_mix = _parse_regional_mix(d.pop("regional_mix", UNSET))

        def _parse_emoji_usage(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        emoji_usage = _parse_emoji_usage(d.pop("emoji_usage", UNSET))

        def _parse_verbosity(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        verbosity = _parse_verbosity(d.pop("verbosity", UNSET))

        persona_create = cls(
            name=name,
            description=description,
            gender=gender,
            age_group=age_group,
            location=location,
            profession=profession,
            personality=personality,
            communication_style=communication_style,
            accent=accent,
            multilingual=multilingual,
            language=language,
            conversation_speed=conversation_speed,
            background_sound=background_sound,
            finished_speaking_sensitivity=finished_speaking_sensitivity,
            interrupt_sensitivity=interrupt_sensitivity,
            keywords=keywords,
            custom_properties=custom_properties,
            additional_instruction=additional_instruction,
            simulation_type=simulation_type,
            tone=tone,
            punctuation=punctuation,
            slang_usage=slang_usage,
            typos_frequency=typos_frequency,
            regional_mix=regional_mix,
            emoji_usage=emoji_usage,
            verbosity=verbosity,
        )

        persona_create.additional_properties = d
        return persona_create

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
