from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.agent_definition_create_request_agent_type import (
    AgentDefinitionCreateRequestAgentType,
)
from ..models.agent_definition_create_request_authentication_method import (
    AgentDefinitionCreateRequestAuthenticationMethod,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_definition_create_request_livekit_config_json import (
        AgentDefinitionCreateRequestLivekitConfigJson,
    )
    from ..models.agent_definition_create_request_model_details import (
        AgentDefinitionCreateRequestModelDetails,
    )
    from ..models.agent_definition_create_request_websocket_headers import (
        AgentDefinitionCreateRequestWebsocketHeaders,
    )


T = TypeVar("T", bound="AgentDefinitionCreateRequest")


@_attrs_define
class AgentDefinitionCreateRequest:
    """
    Attributes:
        agent_name (str):
        agent_type (AgentDefinitionCreateRequestAgentType): The type of agent. One of: voice, text.
        commit_message (str):
        inbound (bool | Unset):  Default: True.
        description (str | Unset):  Default: ''.
        provider (None | str | Unset):
        api_key (None | str | Unset):
        assistant_id (None | str | Unset):
        authentication_method (AgentDefinitionCreateRequestAuthenticationMethod | Unset):
        language (None | str | Unset):
        languages (list[str] | None | Unset):
        contact_number (None | str | Unset):
        knowledge_base (None | Unset | UUID):
        observability_enabled (bool | Unset):  Default: False.
        model (None | str | Unset):
        model_details (AgentDefinitionCreateRequestModelDetails | Unset):
        websocket_url (None | str | Unset):
        websocket_headers (AgentDefinitionCreateRequestWebsocketHeaders | Unset):
        replay_session_id (None | Unset | UUID):
        livekit_url (None | str | Unset):
        livekit_api_key (None | str | Unset):
        livekit_api_secret (None | str | Unset):
        livekit_agent_name (None | str | Unset):
        livekit_config_json (AgentDefinitionCreateRequestLivekitConfigJson | Unset):
        livekit_max_concurrency (int | None | Unset):
    """

    agent_name: str
    agent_type: AgentDefinitionCreateRequestAgentType
    commit_message: str
    inbound: bool | Unset = True
    description: str | Unset = ""
    provider: None | str | Unset = UNSET
    api_key: None | str | Unset = UNSET
    assistant_id: None | str | Unset = UNSET
    authentication_method: AgentDefinitionCreateRequestAuthenticationMethod | Unset = (
        UNSET
    )
    language: None | str | Unset = UNSET
    languages: list[str] | None | Unset = UNSET
    contact_number: None | str | Unset = UNSET
    knowledge_base: None | Unset | UUID = UNSET
    observability_enabled: bool | Unset = False
    model: None | str | Unset = UNSET
    model_details: AgentDefinitionCreateRequestModelDetails | Unset = UNSET
    websocket_url: None | str | Unset = UNSET
    websocket_headers: AgentDefinitionCreateRequestWebsocketHeaders | Unset = UNSET
    replay_session_id: None | Unset | UUID = UNSET
    livekit_url: None | str | Unset = UNSET
    livekit_api_key: None | str | Unset = UNSET
    livekit_api_secret: None | str | Unset = UNSET
    livekit_agent_name: None | str | Unset = UNSET
    livekit_config_json: AgentDefinitionCreateRequestLivekitConfigJson | Unset = UNSET
    livekit_max_concurrency: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_name = self.agent_name

        agent_type = self.agent_type.value

        commit_message = self.commit_message

        inbound = self.inbound

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

        knowledge_base: None | str | Unset
        if isinstance(self.knowledge_base, Unset):
            knowledge_base = UNSET
        elif isinstance(self.knowledge_base, UUID):
            knowledge_base = str(self.knowledge_base)
        else:
            knowledge_base = self.knowledge_base

        observability_enabled = self.observability_enabled

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        model_details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.model_details, Unset):
            model_details = self.model_details.to_dict()

        websocket_url: None | str | Unset
        if isinstance(self.websocket_url, Unset):
            websocket_url = UNSET
        else:
            websocket_url = self.websocket_url

        websocket_headers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.websocket_headers, Unset):
            websocket_headers = self.websocket_headers.to_dict()

        replay_session_id: None | str | Unset
        if isinstance(self.replay_session_id, Unset):
            replay_session_id = UNSET
        elif isinstance(self.replay_session_id, UUID):
            replay_session_id = str(self.replay_session_id)
        else:
            replay_session_id = self.replay_session_id

        livekit_url: None | str | Unset
        if isinstance(self.livekit_url, Unset):
            livekit_url = UNSET
        else:
            livekit_url = self.livekit_url

        livekit_api_key: None | str | Unset
        if isinstance(self.livekit_api_key, Unset):
            livekit_api_key = UNSET
        else:
            livekit_api_key = self.livekit_api_key

        livekit_api_secret: None | str | Unset
        if isinstance(self.livekit_api_secret, Unset):
            livekit_api_secret = UNSET
        else:
            livekit_api_secret = self.livekit_api_secret

        livekit_agent_name: None | str | Unset
        if isinstance(self.livekit_agent_name, Unset):
            livekit_agent_name = UNSET
        else:
            livekit_agent_name = self.livekit_agent_name

        livekit_config_json: dict[str, Any] | Unset = UNSET
        if not isinstance(self.livekit_config_json, Unset):
            livekit_config_json = self.livekit_config_json.to_dict()

        livekit_max_concurrency: int | None | Unset
        if isinstance(self.livekit_max_concurrency, Unset):
            livekit_max_concurrency = UNSET
        else:
            livekit_max_concurrency = self.livekit_max_concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "agent_name": agent_name,
                "agent_type": agent_type,
                "commit_message": commit_message,
            }
        )
        if inbound is not UNSET:
            field_dict["inbound"] = inbound
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
        if knowledge_base is not UNSET:
            field_dict["knowledge_base"] = knowledge_base
        if observability_enabled is not UNSET:
            field_dict["observability_enabled"] = observability_enabled
        if model is not UNSET:
            field_dict["model"] = model
        if model_details is not UNSET:
            field_dict["model_details"] = model_details
        if websocket_url is not UNSET:
            field_dict["websocket_url"] = websocket_url
        if websocket_headers is not UNSET:
            field_dict["websocket_headers"] = websocket_headers
        if replay_session_id is not UNSET:
            field_dict["replay_session_id"] = replay_session_id
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_definition_create_request_livekit_config_json import (
            AgentDefinitionCreateRequestLivekitConfigJson,
        )
        from ..models.agent_definition_create_request_model_details import (
            AgentDefinitionCreateRequestModelDetails,
        )
        from ..models.agent_definition_create_request_websocket_headers import (
            AgentDefinitionCreateRequestWebsocketHeaders,
        )

        d = dict(src_dict)
        agent_name = d.pop("agent_name")

        agent_type = AgentDefinitionCreateRequestAgentType(d.pop("agent_type"))

        commit_message = d.pop("commit_message")

        inbound = d.pop("inbound", UNSET)

        description = d.pop("description", UNSET)

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
        authentication_method: AgentDefinitionCreateRequestAuthenticationMethod | Unset
        if isinstance(_authentication_method, Unset):
            authentication_method = UNSET
        else:
            authentication_method = AgentDefinitionCreateRequestAuthenticationMethod(
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

        observability_enabled = d.pop("observability_enabled", UNSET)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _model_details = d.pop("model_details", UNSET)
        model_details: AgentDefinitionCreateRequestModelDetails | Unset
        if isinstance(_model_details, Unset):
            model_details = UNSET
        else:
            model_details = AgentDefinitionCreateRequestModelDetails.from_dict(
                _model_details
            )

        def _parse_websocket_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        websocket_url = _parse_websocket_url(d.pop("websocket_url", UNSET))

        _websocket_headers = d.pop("websocket_headers", UNSET)
        websocket_headers: AgentDefinitionCreateRequestWebsocketHeaders | Unset
        if isinstance(_websocket_headers, Unset):
            websocket_headers = UNSET
        else:
            websocket_headers = AgentDefinitionCreateRequestWebsocketHeaders.from_dict(
                _websocket_headers
            )

        def _parse_replay_session_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                replay_session_id_type_0 = UUID(data)

                return replay_session_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        replay_session_id = _parse_replay_session_id(d.pop("replay_session_id", UNSET))

        def _parse_livekit_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        livekit_url = _parse_livekit_url(d.pop("livekit_url", UNSET))

        def _parse_livekit_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        livekit_api_key = _parse_livekit_api_key(d.pop("livekit_api_key", UNSET))

        def _parse_livekit_api_secret(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        livekit_api_secret = _parse_livekit_api_secret(
            d.pop("livekit_api_secret", UNSET)
        )

        def _parse_livekit_agent_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        livekit_agent_name = _parse_livekit_agent_name(
            d.pop("livekit_agent_name", UNSET)
        )

        _livekit_config_json = d.pop("livekit_config_json", UNSET)
        livekit_config_json: AgentDefinitionCreateRequestLivekitConfigJson | Unset
        if isinstance(_livekit_config_json, Unset):
            livekit_config_json = UNSET
        else:
            livekit_config_json = (
                AgentDefinitionCreateRequestLivekitConfigJson.from_dict(
                    _livekit_config_json
                )
            )

        def _parse_livekit_max_concurrency(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        livekit_max_concurrency = _parse_livekit_max_concurrency(
            d.pop("livekit_max_concurrency", UNSET)
        )

        agent_definition_create_request = cls(
            agent_name=agent_name,
            agent_type=agent_type,
            commit_message=commit_message,
            inbound=inbound,
            description=description,
            provider=provider,
            api_key=api_key,
            assistant_id=assistant_id,
            authentication_method=authentication_method,
            language=language,
            languages=languages,
            contact_number=contact_number,
            knowledge_base=knowledge_base,
            observability_enabled=observability_enabled,
            model=model,
            model_details=model_details,
            websocket_url=websocket_url,
            websocket_headers=websocket_headers,
            replay_session_id=replay_session_id,
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_api_secret=livekit_api_secret,
            livekit_agent_name=livekit_agent_name,
            livekit_config_json=livekit_config_json,
            livekit_max_concurrency=livekit_max_concurrency,
        )

        agent_definition_create_request.additional_properties = d
        return agent_definition_create_request

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
