from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.persona_emoji_usage import PersonaEmojiUsage
from ..models.persona_persona_type import PersonaPersonaType
from ..models.persona_punctuation import PersonaPunctuation
from ..models.persona_regional_mix import PersonaRegionalMix
from ..models.persona_simulation_type import PersonaSimulationType
from ..models.persona_slang_usage import PersonaSlangUsage
from ..models.persona_tone import PersonaTone
from ..models.persona_typos_frequency import PersonaTyposFrequency
from ..models.persona_verbosity import PersonaVerbosity
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.persona_accent import PersonaAccent
    from ..models.persona_age_group import PersonaAgeGroup
    from ..models.persona_communication_style import PersonaCommunicationStyle
    from ..models.persona_conversation_speed import PersonaConversationSpeed
    from ..models.persona_custom_properties import PersonaCustomProperties
    from ..models.persona_finished_speaking_sensitivity import (
        PersonaFinishedSpeakingSensitivity,
    )
    from ..models.persona_gender import PersonaGender
    from ..models.persona_interrupt_sensitivity import PersonaInterruptSensitivity
    from ..models.persona_keywords import PersonaKeywords
    from ..models.persona_languages import PersonaLanguages
    from ..models.persona_location import PersonaLocation
    from ..models.persona_metadata import PersonaMetadata
    from ..models.persona_occupation import PersonaOccupation
    from ..models.persona_personality import PersonaPersonality


T = TypeVar("T", bound="Persona")


@_attrs_define
class Persona:
    """
    Attributes:
        name (str): Name of the persona
        id (UUID | Unset):
        persona_type (PersonaPersonaType | Unset): Type of persona (system or workspace-level)
        persona_type_display (str | Unset):
        description (None | str | Unset): Description of the persona
        gender (PersonaGender | Unset): List of genders for the persona (e.g., ['male'], ['female'])
        age_group (PersonaAgeGroup | Unset): List of age groups for the persona (e.g., ['18-25'], ['25-32'])
        occupation (PersonaOccupation | Unset): List of occupations/professions for the persona (e.g., ['Engineer'],
            ['Teacher'])
        location (PersonaLocation | Unset): List of locations for the persona (e.g., ['United States'], ['Canada'])
        personality (PersonaPersonality | Unset): List of personality types for the persona (e.g., ['Friendly and
            cooperative'])
        communication_style (PersonaCommunicationStyle | Unset): List of communication styles for the persona (e.g.,
            ['Direct and concise'])
        multilingual (bool | None | Unset): Whether the persona supports multiple languages
        languages (PersonaLanguages | Unset): List of languages the persona speaks (e.g., ['English', 'Hindi'])
        accent (PersonaAccent | Unset): List of accents for the persona (e.g., ['American'], ['Australian'])
        conversation_speed (PersonaConversationSpeed | Unset): List of conversation speeds (e.g., ['1.0'], ['1.25'])
        background_sound (bool | None | Unset): Whether background sound is enabled (null=not specified, True/False for
            enabled/disabled)
        finished_speaking_sensitivity (PersonaFinishedSpeakingSensitivity | Unset): List of sensitivities for detecting
            when persona finished speaking (e.g., ['5'], ['6'])
        interrupt_sensitivity (PersonaInterruptSensitivity | Unset): List of sensitivities for allowing interruptions
            (e.g., ['5'], ['6'])
        keywords (PersonaKeywords | Unset): List of keywords/tags describing the persona (e.g., ['Knowledgeable',
            'Patient', 'Helpful'])
        metadata (PersonaMetadata | Unset): Additional metadata for the persona (speech clarity, base emotion, etc.)
        additional_instruction (None | str | Unset): Additional instructions for how this persona should behave
        is_default (bool | None | Unset): Whether this is a default/recommended persona
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        profession (list[str] | None | Unset):
        language (list[str] | None | Unset):
        custom_properties (PersonaCustomProperties | Unset):
        simulation_type (PersonaSimulationType | Unset): Type of simulation for the persona
        punctuation (PersonaPunctuation | Unset): Punctuation style for the persona
        slang_usage (PersonaSlangUsage | Unset): Slang usage for the persona
        typos_frequency (PersonaTyposFrequency | Unset): Typos frequency for the persona
        regional_mix (PersonaRegionalMix | Unset): Regional mix for the persona
        emoji_usage (PersonaEmojiUsage | Unset): Emoji usage for the persona
        tone (PersonaTone | Unset): Tone for the persona
        verbosity (PersonaVerbosity | Unset): Verbosity for the persona
    """

    name: str
    id: UUID | Unset = UNSET
    persona_type: PersonaPersonaType | Unset = UNSET
    persona_type_display: str | Unset = UNSET
    description: None | str | Unset = UNSET
    gender: PersonaGender | Unset = UNSET
    age_group: PersonaAgeGroup | Unset = UNSET
    occupation: PersonaOccupation | Unset = UNSET
    location: PersonaLocation | Unset = UNSET
    personality: PersonaPersonality | Unset = UNSET
    communication_style: PersonaCommunicationStyle | Unset = UNSET
    multilingual: bool | None | Unset = UNSET
    languages: PersonaLanguages | Unset = UNSET
    accent: PersonaAccent | Unset = UNSET
    conversation_speed: PersonaConversationSpeed | Unset = UNSET
    background_sound: bool | None | Unset = UNSET
    finished_speaking_sensitivity: PersonaFinishedSpeakingSensitivity | Unset = UNSET
    interrupt_sensitivity: PersonaInterruptSensitivity | Unset = UNSET
    keywords: PersonaKeywords | Unset = UNSET
    metadata: PersonaMetadata | Unset = UNSET
    additional_instruction: None | str | Unset = UNSET
    is_default: bool | None | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    profession: list[str] | None | Unset = UNSET
    language: list[str] | None | Unset = UNSET
    custom_properties: PersonaCustomProperties | Unset = UNSET
    simulation_type: PersonaSimulationType | Unset = UNSET
    punctuation: PersonaPunctuation | Unset = UNSET
    slang_usage: PersonaSlangUsage | Unset = UNSET
    typos_frequency: PersonaTyposFrequency | Unset = UNSET
    regional_mix: PersonaRegionalMix | Unset = UNSET
    emoji_usage: PersonaEmojiUsage | Unset = UNSET
    tone: PersonaTone | Unset = UNSET
    verbosity: PersonaVerbosity | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        persona_type: str | Unset = UNSET
        if not isinstance(self.persona_type, Unset):
            persona_type = self.persona_type.value

        persona_type_display = self.persona_type_display

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        gender: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gender, Unset):
            gender = self.gender.to_dict()

        age_group: dict[str, Any] | Unset = UNSET
        if not isinstance(self.age_group, Unset):
            age_group = self.age_group.to_dict()

        occupation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.occupation, Unset):
            occupation = self.occupation.to_dict()

        location: dict[str, Any] | Unset = UNSET
        if not isinstance(self.location, Unset):
            location = self.location.to_dict()

        personality: dict[str, Any] | Unset = UNSET
        if not isinstance(self.personality, Unset):
            personality = self.personality.to_dict()

        communication_style: dict[str, Any] | Unset = UNSET
        if not isinstance(self.communication_style, Unset):
            communication_style = self.communication_style.to_dict()

        multilingual: bool | None | Unset
        if isinstance(self.multilingual, Unset):
            multilingual = UNSET
        else:
            multilingual = self.multilingual

        languages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.languages, Unset):
            languages = self.languages.to_dict()

        accent: dict[str, Any] | Unset = UNSET
        if not isinstance(self.accent, Unset):
            accent = self.accent.to_dict()

        conversation_speed: dict[str, Any] | Unset = UNSET
        if not isinstance(self.conversation_speed, Unset):
            conversation_speed = self.conversation_speed.to_dict()

        background_sound: bool | None | Unset
        if isinstance(self.background_sound, Unset):
            background_sound = UNSET
        else:
            background_sound = self.background_sound

        finished_speaking_sensitivity: dict[str, Any] | Unset = UNSET
        if not isinstance(self.finished_speaking_sensitivity, Unset):
            finished_speaking_sensitivity = self.finished_speaking_sensitivity.to_dict()

        interrupt_sensitivity: dict[str, Any] | Unset = UNSET
        if not isinstance(self.interrupt_sensitivity, Unset):
            interrupt_sensitivity = self.interrupt_sensitivity.to_dict()

        keywords: dict[str, Any] | Unset = UNSET
        if not isinstance(self.keywords, Unset):
            keywords = self.keywords.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        additional_instruction: None | str | Unset
        if isinstance(self.additional_instruction, Unset):
            additional_instruction = UNSET
        else:
            additional_instruction = self.additional_instruction

        is_default: bool | None | Unset
        if isinstance(self.is_default, Unset):
            is_default = UNSET
        else:
            is_default = self.is_default

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        profession: list[str] | None | Unset
        if isinstance(self.profession, Unset):
            profession = UNSET
        elif isinstance(self.profession, list):
            profession = self.profession

        else:
            profession = self.profession

        language: list[str] | None | Unset
        if isinstance(self.language, Unset):
            language = UNSET
        elif isinstance(self.language, list):
            language = self.language

        else:
            language = self.language

        custom_properties: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_properties, Unset):
            custom_properties = self.custom_properties.to_dict()

        simulation_type: str | Unset = UNSET
        if not isinstance(self.simulation_type, Unset):
            simulation_type = self.simulation_type.value

        punctuation: str | Unset = UNSET
        if not isinstance(self.punctuation, Unset):
            punctuation = self.punctuation.value

        slang_usage: str | Unset = UNSET
        if not isinstance(self.slang_usage, Unset):
            slang_usage = self.slang_usage.value

        typos_frequency: str | Unset = UNSET
        if not isinstance(self.typos_frequency, Unset):
            typos_frequency = self.typos_frequency.value

        regional_mix: str | Unset = UNSET
        if not isinstance(self.regional_mix, Unset):
            regional_mix = self.regional_mix.value

        emoji_usage: str | Unset = UNSET
        if not isinstance(self.emoji_usage, Unset):
            emoji_usage = self.emoji_usage.value

        tone: str | Unset = UNSET
        if not isinstance(self.tone, Unset):
            tone = self.tone.value

        verbosity: str | Unset = UNSET
        if not isinstance(self.verbosity, Unset):
            verbosity = self.verbosity.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if persona_type is not UNSET:
            field_dict["persona_type"] = persona_type
        if persona_type_display is not UNSET:
            field_dict["persona_type_display"] = persona_type_display
        if description is not UNSET:
            field_dict["description"] = description
        if gender is not UNSET:
            field_dict["gender"] = gender
        if age_group is not UNSET:
            field_dict["age_group"] = age_group
        if occupation is not UNSET:
            field_dict["occupation"] = occupation
        if location is not UNSET:
            field_dict["location"] = location
        if personality is not UNSET:
            field_dict["personality"] = personality
        if communication_style is not UNSET:
            field_dict["communication_style"] = communication_style
        if multilingual is not UNSET:
            field_dict["multilingual"] = multilingual
        if languages is not UNSET:
            field_dict["languages"] = languages
        if accent is not UNSET:
            field_dict["accent"] = accent
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
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if additional_instruction is not UNSET:
            field_dict["additional_instruction"] = additional_instruction
        if is_default is not UNSET:
            field_dict["is_default"] = is_default
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if profession is not UNSET:
            field_dict["profession"] = profession
        if language is not UNSET:
            field_dict["language"] = language
        if custom_properties is not UNSET:
            field_dict["custom_properties"] = custom_properties
        if simulation_type is not UNSET:
            field_dict["simulation_type"] = simulation_type
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
        if tone is not UNSET:
            field_dict["tone"] = tone
        if verbosity is not UNSET:
            field_dict["verbosity"] = verbosity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.persona_accent import PersonaAccent
        from ..models.persona_age_group import PersonaAgeGroup
        from ..models.persona_communication_style import PersonaCommunicationStyle
        from ..models.persona_conversation_speed import PersonaConversationSpeed
        from ..models.persona_custom_properties import PersonaCustomProperties
        from ..models.persona_finished_speaking_sensitivity import (
            PersonaFinishedSpeakingSensitivity,
        )
        from ..models.persona_gender import PersonaGender
        from ..models.persona_interrupt_sensitivity import PersonaInterruptSensitivity
        from ..models.persona_keywords import PersonaKeywords
        from ..models.persona_languages import PersonaLanguages
        from ..models.persona_location import PersonaLocation
        from ..models.persona_metadata import PersonaMetadata
        from ..models.persona_occupation import PersonaOccupation
        from ..models.persona_personality import PersonaPersonality

        d = dict(src_dict)
        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _persona_type = d.pop("persona_type", UNSET)
        persona_type: PersonaPersonaType | Unset
        if isinstance(_persona_type, Unset):
            persona_type = UNSET
        else:
            persona_type = PersonaPersonaType(_persona_type)

        persona_type_display = d.pop("persona_type_display", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _gender = d.pop("gender", UNSET)
        gender: PersonaGender | Unset
        if isinstance(_gender, Unset):
            gender = UNSET
        else:
            gender = PersonaGender.from_dict(_gender)

        _age_group = d.pop("age_group", UNSET)
        age_group: PersonaAgeGroup | Unset
        if isinstance(_age_group, Unset):
            age_group = UNSET
        else:
            age_group = PersonaAgeGroup.from_dict(_age_group)

        _occupation = d.pop("occupation", UNSET)
        occupation: PersonaOccupation | Unset
        if isinstance(_occupation, Unset):
            occupation = UNSET
        else:
            occupation = PersonaOccupation.from_dict(_occupation)

        _location = d.pop("location", UNSET)
        location: PersonaLocation | Unset
        if isinstance(_location, Unset):
            location = UNSET
        else:
            location = PersonaLocation.from_dict(_location)

        _personality = d.pop("personality", UNSET)
        personality: PersonaPersonality | Unset
        if isinstance(_personality, Unset):
            personality = UNSET
        else:
            personality = PersonaPersonality.from_dict(_personality)

        _communication_style = d.pop("communication_style", UNSET)
        communication_style: PersonaCommunicationStyle | Unset
        if isinstance(_communication_style, Unset):
            communication_style = UNSET
        else:
            communication_style = PersonaCommunicationStyle.from_dict(
                _communication_style
            )

        def _parse_multilingual(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        multilingual = _parse_multilingual(d.pop("multilingual", UNSET))

        _languages = d.pop("languages", UNSET)
        languages: PersonaLanguages | Unset
        if isinstance(_languages, Unset):
            languages = UNSET
        else:
            languages = PersonaLanguages.from_dict(_languages)

        _accent = d.pop("accent", UNSET)
        accent: PersonaAccent | Unset
        if isinstance(_accent, Unset):
            accent = UNSET
        else:
            accent = PersonaAccent.from_dict(_accent)

        _conversation_speed = d.pop("conversation_speed", UNSET)
        conversation_speed: PersonaConversationSpeed | Unset
        if isinstance(_conversation_speed, Unset):
            conversation_speed = UNSET
        else:
            conversation_speed = PersonaConversationSpeed.from_dict(_conversation_speed)

        def _parse_background_sound(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        background_sound = _parse_background_sound(d.pop("background_sound", UNSET))

        _finished_speaking_sensitivity = d.pop("finished_speaking_sensitivity", UNSET)
        finished_speaking_sensitivity: PersonaFinishedSpeakingSensitivity | Unset
        if isinstance(_finished_speaking_sensitivity, Unset):
            finished_speaking_sensitivity = UNSET
        else:
            finished_speaking_sensitivity = (
                PersonaFinishedSpeakingSensitivity.from_dict(
                    _finished_speaking_sensitivity
                )
            )

        _interrupt_sensitivity = d.pop("interrupt_sensitivity", UNSET)
        interrupt_sensitivity: PersonaInterruptSensitivity | Unset
        if isinstance(_interrupt_sensitivity, Unset):
            interrupt_sensitivity = UNSET
        else:
            interrupt_sensitivity = PersonaInterruptSensitivity.from_dict(
                _interrupt_sensitivity
            )

        _keywords = d.pop("keywords", UNSET)
        keywords: PersonaKeywords | Unset
        if isinstance(_keywords, Unset):
            keywords = UNSET
        else:
            keywords = PersonaKeywords.from_dict(_keywords)

        _metadata = d.pop("metadata", UNSET)
        metadata: PersonaMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PersonaMetadata.from_dict(_metadata)

        def _parse_additional_instruction(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_instruction = _parse_additional_instruction(
            d.pop("additional_instruction", UNSET)
        )

        def _parse_is_default(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_default = _parse_is_default(d.pop("is_default", UNSET))

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

        _custom_properties = d.pop("custom_properties", UNSET)
        custom_properties: PersonaCustomProperties | Unset
        if isinstance(_custom_properties, Unset):
            custom_properties = UNSET
        else:
            custom_properties = PersonaCustomProperties.from_dict(_custom_properties)

        _simulation_type = d.pop("simulation_type", UNSET)
        simulation_type: PersonaSimulationType | Unset
        if isinstance(_simulation_type, Unset):
            simulation_type = UNSET
        else:
            simulation_type = PersonaSimulationType(_simulation_type)

        _punctuation = d.pop("punctuation", UNSET)
        punctuation: PersonaPunctuation | Unset
        if isinstance(_punctuation, Unset):
            punctuation = UNSET
        else:
            punctuation = PersonaPunctuation(_punctuation)

        _slang_usage = d.pop("slang_usage", UNSET)
        slang_usage: PersonaSlangUsage | Unset
        if isinstance(_slang_usage, Unset):
            slang_usage = UNSET
        else:
            slang_usage = PersonaSlangUsage(_slang_usage)

        _typos_frequency = d.pop("typos_frequency", UNSET)
        typos_frequency: PersonaTyposFrequency | Unset
        if isinstance(_typos_frequency, Unset):
            typos_frequency = UNSET
        else:
            typos_frequency = PersonaTyposFrequency(_typos_frequency)

        _regional_mix = d.pop("regional_mix", UNSET)
        regional_mix: PersonaRegionalMix | Unset
        if isinstance(_regional_mix, Unset):
            regional_mix = UNSET
        else:
            regional_mix = PersonaRegionalMix(_regional_mix)

        _emoji_usage = d.pop("emoji_usage", UNSET)
        emoji_usage: PersonaEmojiUsage | Unset
        if isinstance(_emoji_usage, Unset):
            emoji_usage = UNSET
        else:
            emoji_usage = PersonaEmojiUsage(_emoji_usage)

        _tone = d.pop("tone", UNSET)
        tone: PersonaTone | Unset
        if isinstance(_tone, Unset):
            tone = UNSET
        else:
            tone = PersonaTone(_tone)

        _verbosity = d.pop("verbosity", UNSET)
        verbosity: PersonaVerbosity | Unset
        if isinstance(_verbosity, Unset):
            verbosity = UNSET
        else:
            verbosity = PersonaVerbosity(_verbosity)

        persona = cls(
            name=name,
            id=id,
            persona_type=persona_type,
            persona_type_display=persona_type_display,
            description=description,
            gender=gender,
            age_group=age_group,
            occupation=occupation,
            location=location,
            personality=personality,
            communication_style=communication_style,
            multilingual=multilingual,
            languages=languages,
            accent=accent,
            conversation_speed=conversation_speed,
            background_sound=background_sound,
            finished_speaking_sensitivity=finished_speaking_sensitivity,
            interrupt_sensitivity=interrupt_sensitivity,
            keywords=keywords,
            metadata=metadata,
            additional_instruction=additional_instruction,
            is_default=is_default,
            created_at=created_at,
            updated_at=updated_at,
            profession=profession,
            language=language,
            custom_properties=custom_properties,
            simulation_type=simulation_type,
            punctuation=punctuation,
            slang_usage=slang_usage,
            typos_frequency=typos_frequency,
            regional_mix=regional_mix,
            emoji_usage=emoji_usage,
            tone=tone,
            verbosity=verbosity,
        )

        persona.additional_properties = d
        return persona

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
