from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.agent_definition_response_agent_type import (
    AgentDefinitionResponseAgentType,
)
from ..models.agent_definition_response_authentication_method import (
    AgentDefinitionResponseAuthenticationMethod,
)
from ..models.agent_definition_response_language import AgentDefinitionResponseLanguage
from ..models.agent_definition_response_languages import (
    AgentDefinitionResponseLanguages,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_definition_response_model_details import (
        AgentDefinitionResponseModelDetails,
    )
    from ..models.agent_definition_response_websocket_headers import (
        AgentDefinitionResponseWebsocketHeaders,
    )


T = TypeVar("T", bound="AgentDefinitionResponse")


@_attrs_define
class AgentDefinitionResponse:
    """
    Attributes:
        id (UUID | Unset):
        agent_name (str | Unset): Name of the AI agent
        agent_type (AgentDefinitionResponseAgentType | Unset):
        contact_number (None | str | Unset): Phone number associated with the AI agent
        inbound (bool | Unset): Whether the agent handles inbound calls
        description (str | Unset): Detailed description of the AI agent's purpose and capabilities
        assistant_id (None | str | Unset): External identifier for the assistant
        provider (None | str | Unset): Provider of the AI agent
        language (AgentDefinitionResponseLanguage | Unset): Language of the agent
        languages (list[AgentDefinitionResponseLanguages] | None | Unset):
        authentication_method (AgentDefinitionResponseAuthenticationMethod | Unset):
        websocket_url (None | str | Unset): WebSocket URL for real-time communication with the agent
        websocket_headers (AgentDefinitionResponseWebsocketHeaders | Unset): Headers to be sent to the websocket server
        workspace (None | Unset | UUID):
        knowledge_base (None | Unset | UUID):
        organization (UUID | Unset): Organization this agent definition belongs to
        api_key (None | str | Unset): API key for the agent
        observability_provider (None | Unset | UUID):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        model (None | str | Unset): Model of the agent
        model_details (AgentDefinitionResponseModelDetails | Unset): Details of the model
        livekit_url (str | Unset):
        livekit_api_key (str | Unset):
        livekit_agent_name (str | Unset):
        livekit_config_json (str | Unset):
        livekit_max_concurrency (str | Unset):
    """

    id: UUID | Unset = UNSET
    agent_name: str | Unset = UNSET
    agent_type: AgentDefinitionResponseAgentType | Unset = UNSET
    contact_number: None | str | Unset = UNSET
    inbound: bool | Unset = UNSET
    description: str | Unset = UNSET
    assistant_id: None | str | Unset = UNSET
    provider: None | str | Unset = UNSET
    language: AgentDefinitionResponseLanguage | Unset = UNSET
    languages: list[AgentDefinitionResponseLanguages] | None | Unset = UNSET
    authentication_method: AgentDefinitionResponseAuthenticationMethod | Unset = UNSET
    websocket_url: None | str | Unset = UNSET
    websocket_headers: AgentDefinitionResponseWebsocketHeaders | Unset = UNSET
    workspace: None | Unset | UUID = UNSET
    knowledge_base: None | Unset | UUID = UNSET
    organization: UUID | Unset = UNSET
    api_key: None | str | Unset = UNSET
    observability_provider: None | Unset | UUID = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    model: None | str | Unset = UNSET
    model_details: AgentDefinitionResponseModelDetails | Unset = UNSET
    livekit_url: str | Unset = UNSET
    livekit_api_key: str | Unset = UNSET
    livekit_agent_name: str | Unset = UNSET
    livekit_config_json: str | Unset = UNSET
    livekit_max_concurrency: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        agent_name = self.agent_name

        agent_type: str | Unset = UNSET
        if not isinstance(self.agent_type, Unset):
            agent_type = self.agent_type.value

        contact_number: None | str | Unset
        if isinstance(self.contact_number, Unset):
            contact_number = UNSET
        else:
            contact_number = self.contact_number

        inbound = self.inbound

        description = self.description

        assistant_id: None | str | Unset
        if isinstance(self.assistant_id, Unset):
            assistant_id = UNSET
        else:
            assistant_id = self.assistant_id

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        else:
            provider = self.provider

        language: str | Unset = UNSET
        if not isinstance(self.language, Unset):
            language = self.language.value

        languages: list[str] | None | Unset
        if isinstance(self.languages, Unset):
            languages = UNSET
        elif isinstance(self.languages, list):
            languages = []
            for languages_type_0_item_data in self.languages:
                languages_type_0_item = languages_type_0_item_data.value
                languages.append(languages_type_0_item)

        else:
            languages = self.languages

        authentication_method: str | Unset = UNSET
        if not isinstance(self.authentication_method, Unset):
            authentication_method = self.authentication_method.value

        websocket_url: None | str | Unset
        if isinstance(self.websocket_url, Unset):
            websocket_url = UNSET
        else:
            websocket_url = self.websocket_url

        websocket_headers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.websocket_headers, Unset):
            websocket_headers = self.websocket_headers.to_dict()

        workspace: None | str | Unset
        if isinstance(self.workspace, Unset):
            workspace = UNSET
        elif isinstance(self.workspace, UUID):
            workspace = str(self.workspace)
        else:
            workspace = self.workspace

        knowledge_base: None | str | Unset
        if isinstance(self.knowledge_base, Unset):
            knowledge_base = UNSET
        elif isinstance(self.knowledge_base, UUID):
            knowledge_base = str(self.knowledge_base)
        else:
            knowledge_base = self.knowledge_base

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        observability_provider: None | str | Unset
        if isinstance(self.observability_provider, Unset):
            observability_provider = UNSET
        elif isinstance(self.observability_provider, UUID):
            observability_provider = str(self.observability_provider)
        else:
            observability_provider = self.observability_provider

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

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

        livekit_agent_name = self.livekit_agent_name

        livekit_config_json = self.livekit_config_json

        livekit_max_concurrency = self.livekit_max_concurrency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if agent_name is not UNSET:
            field_dict["agent_name"] = agent_name
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type
        if contact_number is not UNSET:
            field_dict["contact_number"] = contact_number
        if inbound is not UNSET:
            field_dict["inbound"] = inbound
        if description is not UNSET:
            field_dict["description"] = description
        if assistant_id is not UNSET:
            field_dict["assistant_id"] = assistant_id
        if provider is not UNSET:
            field_dict["provider"] = provider
        if language is not UNSET:
            field_dict["language"] = language
        if languages is not UNSET:
            field_dict["languages"] = languages
        if authentication_method is not UNSET:
            field_dict["authentication_method"] = authentication_method
        if websocket_url is not UNSET:
            field_dict["websocket_url"] = websocket_url
        if websocket_headers is not UNSET:
            field_dict["websocket_headers"] = websocket_headers
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if knowledge_base is not UNSET:
            field_dict["knowledge_base"] = knowledge_base
        if organization is not UNSET:
            field_dict["organization"] = organization
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if observability_provider is not UNSET:
            field_dict["observability_provider"] = observability_provider
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if model is not UNSET:
            field_dict["model"] = model
        if model_details is not UNSET:
            field_dict["model_details"] = model_details
        if livekit_url is not UNSET:
            field_dict["livekit_url"] = livekit_url
        if livekit_api_key is not UNSET:
            field_dict["livekit_api_key"] = livekit_api_key
        if livekit_agent_name is not UNSET:
            field_dict["livekit_agent_name"] = livekit_agent_name
        if livekit_config_json is not UNSET:
            field_dict["livekit_config_json"] = livekit_config_json
        if livekit_max_concurrency is not UNSET:
            field_dict["livekit_max_concurrency"] = livekit_max_concurrency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_definition_response_model_details import (
            AgentDefinitionResponseModelDetails,
        )
        from ..models.agent_definition_response_websocket_headers import (
            AgentDefinitionResponseWebsocketHeaders,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        agent_name = d.pop("agent_name", UNSET)

        _agent_type = d.pop("agent_type", UNSET)
        agent_type: AgentDefinitionResponseAgentType | Unset
        if isinstance(_agent_type, Unset):
            agent_type = UNSET
        else:
            agent_type = AgentDefinitionResponseAgentType(_agent_type)

        def _parse_contact_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        contact_number = _parse_contact_number(d.pop("contact_number", UNSET))

        inbound = d.pop("inbound", UNSET)

        description = d.pop("description", UNSET)

        def _parse_assistant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assistant_id = _parse_assistant_id(d.pop("assistant_id", UNSET))

        def _parse_provider(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        _language = d.pop("language", UNSET)
        language: AgentDefinitionResponseLanguage | Unset
        if isinstance(_language, Unset):
            language = UNSET
        else:
            language = AgentDefinitionResponseLanguage(_language)

        def _parse_languages(
            data: object,
        ) -> list[AgentDefinitionResponseLanguages] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                languages_type_0 = []
                _languages_type_0 = data
                for languages_type_0_item_data in _languages_type_0:
                    languages_type_0_item = AgentDefinitionResponseLanguages(
                        languages_type_0_item_data
                    )

                    languages_type_0.append(languages_type_0_item)

                return languages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[AgentDefinitionResponseLanguages] | None | Unset, data)

        languages = _parse_languages(d.pop("languages", UNSET))

        _authentication_method = d.pop("authentication_method", UNSET)
        authentication_method: AgentDefinitionResponseAuthenticationMethod | Unset
        if isinstance(_authentication_method, Unset):
            authentication_method = UNSET
        else:
            authentication_method = AgentDefinitionResponseAuthenticationMethod(
                _authentication_method
            )

        def _parse_websocket_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        websocket_url = _parse_websocket_url(d.pop("websocket_url", UNSET))

        _websocket_headers = d.pop("websocket_headers", UNSET)
        websocket_headers: AgentDefinitionResponseWebsocketHeaders | Unset
        if isinstance(_websocket_headers, Unset):
            websocket_headers = UNSET
        else:
            websocket_headers = AgentDefinitionResponseWebsocketHeaders.from_dict(
                _websocket_headers
            )

        def _parse_workspace(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                workspace_type_0 = UUID(data)

                return workspace_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        workspace = _parse_workspace(d.pop("workspace", UNSET))

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

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_observability_provider(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                observability_provider_type_0 = UUID(data)

                return observability_provider_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        observability_provider = _parse_observability_provider(
            d.pop("observability_provider", UNSET)
        )

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

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        _model_details = d.pop("model_details", UNSET)
        model_details: AgentDefinitionResponseModelDetails | Unset
        if isinstance(_model_details, Unset):
            model_details = UNSET
        else:
            model_details = AgentDefinitionResponseModelDetails.from_dict(
                _model_details
            )

        livekit_url = d.pop("livekit_url", UNSET)

        livekit_api_key = d.pop("livekit_api_key", UNSET)

        livekit_agent_name = d.pop("livekit_agent_name", UNSET)

        livekit_config_json = d.pop("livekit_config_json", UNSET)

        livekit_max_concurrency = d.pop("livekit_max_concurrency", UNSET)

        agent_definition_response = cls(
            id=id,
            agent_name=agent_name,
            agent_type=agent_type,
            contact_number=contact_number,
            inbound=inbound,
            description=description,
            assistant_id=assistant_id,
            provider=provider,
            language=language,
            languages=languages,
            authentication_method=authentication_method,
            websocket_url=websocket_url,
            websocket_headers=websocket_headers,
            workspace=workspace,
            knowledge_base=knowledge_base,
            organization=organization,
            api_key=api_key,
            observability_provider=observability_provider,
            created_at=created_at,
            updated_at=updated_at,
            model=model,
            model_details=model_details,
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_agent_name=livekit_agent_name,
            livekit_config_json=livekit_config_json,
            livekit_max_concurrency=livekit_max_concurrency,
        )

        agent_definition_response.additional_properties = d
        return agent_definition_response

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
