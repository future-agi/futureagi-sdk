from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.agent_version_create_request_agent_type import (
    AgentVersionCreateRequestAgentType,
)
from ..models.agent_version_create_request_authentication_method import (
    AgentVersionCreateRequestAuthenticationMethod,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_version_create_request_livekit_config_json import (
        AgentVersionCreateRequestLivekitConfigJson,
    )
    from ..models.agent_version_create_request_model_details import (
        AgentVersionCreateRequestModelDetails,
    )


T = TypeVar("T", bound="AgentVersionCreateRequest")


@_attrs_define
class AgentVersionCreateRequest:
    """
    Attributes:
        agent_name (str | Unset):
        agent_type (AgentVersionCreateRequestAgentType | Unset):
        description (None | str | Unset):
        provider (None | str | Unset):
        api_key (None | str | Unset):
        assistant_id (None | str | Unset):
        authentication_method (AgentVersionCreateRequestAuthenticationMethod | Unset):
        language (None | str | Unset):
        languages (list[str] | None | Unset):
        contact_number (None | str | Unset):
        inbound (bool | Unset):
        knowledge_base (None | Unset | UUID):
        model (None | str | Unset):
        model_details (AgentVersionCreateRequestModelDetails | Unset):
        livekit_url (str | Unset):
        livekit_api_key (str | Unset):
        livekit_api_secret (str | Unset):
        livekit_agent_name (str | Unset):
        livekit_config_json (AgentVersionCreateRequestLivekitConfigJson | Unset):
        livekit_max_concurrency (int | Unset):
        commit_message (str | Unset):  Default: ''.
        observability_enabled (bool | Unset):  Default: False.
    """

    agent_name: str | Unset = UNSET
    agent_type: AgentVersionCreateRequestAgentType | Unset = UNSET
    description: None | str | Unset = UNSET
    provider: None | str | Unset = UNSET
    api_key: None | str | Unset = UNSET
    assistant_id: None | str | Unset = UNSET
    authentication_method: AgentVersionCreateRequestAuthenticationMethod | Unset = UNSET
    language: None | str | Unset = UNSET
    languages: list[str] | None | Unset = UNSET
    contact_number: None | str | Unset = UNSET
    inbound: bool | Unset = UNSET
    knowledge_base: None | Unset | UUID = UNSET
    model: None | str | Unset = UNSET
    model_details: AgentVersionCreateRequestModelDetails | Unset = UNSET
    livekit_url: str | Unset = UNSET
    livekit_api_key: str | Unset = UNSET
    livekit_api_secret: str | Unset = UNSET
    livekit_agent_name: str | Unset = UNSET
    livekit_config_json: AgentVersionCreateRequestLivekitConfigJson | Unset = UNSET
    livekit_max_concurrency: int | Unset = UNSET
    commit_message: str | Unset = ""
    observability_enabled: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_name = self.agent_name

        agent_type: str | Unset = UNSET
        if not isinstance(self.agent_type, Unset):
            agent_type = self.agent_type.value

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        else:
            provider = self.provider

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        assistant_id: None | str | Unset
        if isinstance(self.assistant_id, Unset):
            assistant_id = UNSET
        else:
            assistant_id = self.assistant_id

        authentication_method: str | Unset = UNSET
        if not isinstance(self.authentication_method, Unset):
            authentication_method = self.authentication_method.value

        language: None | str | Unset
        if isinstance(self.language, Unset):
            language = UNSET
        else:
            language = self.language

        languages: list[str] | None | Unset
        if isinstance(self.languages, Unset):
            languages = UNSET
        elif isinstance(self.languages, list):
            languages = self.languages

        else:
            languages = self.languages

        contact_number: None | str | Unset
        if isinstance(self.contact_number, Unset):
            contact_number = UNSET
        else:
            contact_number = self.contact_number

        inbound = self.inbound

        knowledge_base: None | str | Unset
        if isinstance(self.knowledge_base, Unset):
            knowledge_base = UNSET
        elif isinstance(self.knowledge_base, UUID):
            knowledge_base = str(self.knowledge_base)
        else:
            knowledge_base = self.knowledge_base

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        model_details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model_details, Unset):
            model_details = self.model_details.to_dict()

        livekit_url = self.livekit_url

        livekit_api_key = self.livekit_api_key

        livekit_api_secret = self.livekit_api_secret

        livekit_agent_name = self.livekit_agent_name

        livekit_config_json: dict[str, Any] | Unset = UNSET
        if not isinstance(self.livekit_config_json, Unset):
            livekit_config_json = self.livekit_config_json.to_dict()

        livekit_max_concurrency = self.livekit_max_concurrency

        commit_message = self.commit_message

        observability_enabled = self.observability_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if agent_name is not UNSET:
            field_dict["agent_name"] = agent_name
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type
        if description is not UNSET:
            field_dict["description"] = description
        if provider is not UNSET:
            field_dict["provider"] = provider
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if assistant_id is not UNSET:
            field_dict["assistant_id"] = assistant_id
        if authentication_method is not UNSET:
            field_dict["authentication_method"] = authentication_method
        if language is not UNSET:
            field_dict["language"] = language
        if languages is not UNSET:
            field_dict["languages"] = languages
        if contact_number is not UNSET:
            field_dict["contact_number"] = contact_number
        if inbound is not UNSET:
            field_dict["inbound"] = inbound
        if knowledge_base is not UNSET:
            field_dict["knowledge_base"] = knowledge_base
        if model is not UNSET:
            field_dict["model"] = model
        if model_details is not UNSET:
            field_dict["model_details"] = model_details
        if livekit_url is not UNSET:
            field_dict["livekit_url"] = livekit_url
        if livekit_api_key is not UNSET:
            field_dict["livekit_api_key"] = livekit_api_key
        if livekit_api_secret is not UNSET:
            field_dict["livekit_api_secret"] = livekit_api_secret
        if livekit_agent_name is not UNSET:
            field_dict["livekit_agent_name"] = livekit_agent_name
        if livekit_config_json is not UNSET:
            field_dict["livekit_config_json"] = livekit_config_json
        if livekit_max_concurrency is not UNSET:
            field_dict["livekit_max_concurrency"] = livekit_max_concurrency
        if commit_message is not UNSET:
            field_dict["commit_message"] = commit_message
        if observability_enabled is not UNSET:
            field_dict["observability_enabled"] = observability_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_version_create_request_livekit_config_json import (
            AgentVersionCreateRequestLivekitConfigJson,
        )
        from ..models.agent_version_create_request_model_details import (
            AgentVersionCreateRequestModelDetails,
        )

        d = dict(src_dict)
        agent_name = d.pop("agent_name", UNSET)

        _agent_type = d.pop("agent_type", UNSET)
        agent_type: AgentVersionCreateRequestAgentType | Unset
        if isinstance(_agent_type, Unset):
            agent_type = UNSET
        else:
            agent_type = AgentVersionCreateRequestAgentType(_agent_type)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_provider(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_assistant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assistant_id = _parse_assistant_id(d.pop("assistant_id", UNSET))

        _authentication_method = d.pop("authentication_method", UNSET)
        authentication_method: AgentVersionCreateRequestAuthenticationMethod | Unset
        if isinstance(_authentication_method, Unset):
            authentication_method = UNSET
        else:
            authentication_method = AgentVersionCreateRequestAuthenticationMethod(
                _authentication_method
            )

        def _parse_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        language = _parse_language(d.pop("language", UNSET))

        def _parse_languages(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                languages_type_0 = cast(list[str], data)

                return languages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        languages = _parse_languages(d.pop("languages", UNSET))

        def _parse_contact_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        contact_number = _parse_contact_number(d.pop("contact_number", UNSET))

        inbound = d.pop("inbound", UNSET)

        def _parse_knowledge_base(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                knowledge_base_type_0 = UUID(data)

                return knowledge_base_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        knowledge_base = _parse_knowledge_base(d.pop("knowledge_base", UNSET))

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _model_details = d.pop("model_details", UNSET)
        model_details: AgentVersionCreateRequestModelDetails | Unset
        if isinstance(_model_details, Unset):
            model_details = UNSET
        else:
            model_details = AgentVersionCreateRequestModelDetails.from_dict(
                _model_details
            )

        livekit_url = d.pop("livekit_url", UNSET)

        livekit_api_key = d.pop("livekit_api_key", UNSET)

        livekit_api_secret = d.pop("livekit_api_secret", UNSET)

        livekit_agent_name = d.pop("livekit_agent_name", UNSET)

        _livekit_config_json = d.pop("livekit_config_json", UNSET)
        livekit_config_json: AgentVersionCreateRequestLivekitConfigJson | Unset
        if isinstance(_livekit_config_json, Unset):
            livekit_config_json = UNSET
        else:
            livekit_config_json = AgentVersionCreateRequestLivekitConfigJson.from_dict(
                _livekit_config_json
            )

        livekit_max_concurrency = d.pop("livekit_max_concurrency", UNSET)

        commit_message = d.pop("commit_message", UNSET)

        observability_enabled = d.pop("observability_enabled", UNSET)

        agent_version_create_request = cls(
            agent_name=agent_name,
            agent_type=agent_type,
            description=description,
            provider=provider,
            api_key=api_key,
            assistant_id=assistant_id,
            authentication_method=authentication_method,
            language=language,
            languages=languages,
            contact_number=contact_number,
            inbound=inbound,
            knowledge_base=knowledge_base,
            model=model,
            model_details=model_details,
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_api_secret=livekit_api_secret,
            livekit_agent_name=livekit_agent_name,
            livekit_config_json=livekit_config_json,
            livekit_max_concurrency=livekit_max_concurrency,
            commit_message=commit_message,
            observability_enabled=observability_enabled,
        )

        agent_version_create_request.additional_properties = d
        return agent_version_create_request

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
