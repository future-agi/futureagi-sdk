from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.scenario_create_request_kind import ScenarioCreateRequestKind
from ..models.scenario_create_request_source_type import ScenarioCreateRequestSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column_definition import ColumnDefinition
    from ..models.scenario_create_request_graph import ScenarioCreateRequestGraph


T = TypeVar("T", bound="ScenarioCreateRequest")


@_attrs_define
class ScenarioCreateRequest:
    """
    Attributes:
        name (str):
        description (str | Unset):
        dataset_id (UUID | Unset):
        kind (ScenarioCreateRequestKind | Unset):  Default: ScenarioCreateRequestKind.DATASET.
        script_url (None | str | Unset):
        agent_definition_id (UUID | Unset):
        agent_definition_version_id (None | Unset | UUID):
        custom_instruction (str | Unset):
        no_of_rows (int | Unset):  Default: 20.
        generate_graph (bool | Unset):  Default: False.
        graph (ScenarioCreateRequestGraph | Unset):
        source_type (ScenarioCreateRequestSourceType | Unset):  Default:
            ScenarioCreateRequestSourceType.AGENT_DEFINITION.
        prompt_template_id (None | Unset | UUID):
        prompt_version_id (None | Unset | UUID):
        add_persona_automatically (bool | Unset):  Default: False.
        personas (list[UUID] | Unset):
        custom_columns (list[ColumnDefinition] | Unset):
        agent_name (str | Unset):
        agent_prompt (str | Unset):
        voice_provider (str | Unset):  Default: 'elevenlabs'.
        voice_name (str | Unset):  Default: 'marissa'.
        model (str | Unset):  Default: 'gpt-4'.
        llm_temperature (float | Unset):  Default: 0.7.
        initial_message (str | Unset):
        max_call_duration_in_minutes (int | Unset):  Default: 30.
        interrupt_sensitivity (float | Unset):  Default: 0.5.
        conversation_speed (float | Unset):  Default: 1.0.
        finished_speaking_sensitivity (float | Unset):  Default: 0.5.
        initial_message_delay (int | Unset):  Default: 0.
    """

    name: str
    description: str | Unset = UNSET
    dataset_id: UUID | Unset = UNSET
    kind: ScenarioCreateRequestKind | Unset = ScenarioCreateRequestKind.DATASET
    script_url: None | str | Unset = UNSET
    agent_definition_id: UUID | Unset = UNSET
    agent_definition_version_id: None | Unset | UUID = UNSET
    custom_instruction: str | Unset = UNSET
    no_of_rows: int | Unset = 20
    generate_graph: bool | Unset = False
    graph: ScenarioCreateRequestGraph | Unset = UNSET
    source_type: ScenarioCreateRequestSourceType | Unset = (
        ScenarioCreateRequestSourceType.AGENT_DEFINITION
    )
    prompt_template_id: None | Unset | UUID = UNSET
    prompt_version_id: None | Unset | UUID = UNSET
    add_persona_automatically: bool | Unset = False
    personas: list[UUID] | Unset = UNSET
    custom_columns: list[ColumnDefinition] | Unset = UNSET
    agent_name: str | Unset = UNSET
    agent_prompt: str | Unset = UNSET
    voice_provider: str | Unset = "elevenlabs"
    voice_name: str | Unset = "marissa"
    model: str | Unset = "gpt-4"
    llm_temperature: float | Unset = 0.7
    initial_message: str | Unset = UNSET
    max_call_duration_in_minutes: int | Unset = 30
    interrupt_sensitivity: float | Unset = 0.5
    conversation_speed: float | Unset = 1.0
    finished_speaking_sensitivity: float | Unset = 0.5
    initial_message_delay: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        script_url: None | str | Unset
        if isinstance(self.script_url, Unset):
            script_url = UNSET
        else:
            script_url = self.script_url

        agent_definition_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_id, Unset):
            agent_definition_id = str(self.agent_definition_id)

        agent_definition_version_id: None | str | Unset
        if isinstance(self.agent_definition_version_id, Unset):
            agent_definition_version_id = UNSET
        elif isinstance(self.agent_definition_version_id, UUID):
            agent_definition_version_id = str(self.agent_definition_version_id)
        else:
            agent_definition_version_id = self.agent_definition_version_id

        custom_instruction = self.custom_instruction

        no_of_rows = self.no_of_rows

        generate_graph = self.generate_graph

        graph: dict[str, Any] | Unset = UNSET
        if not isinstance(self.graph, Unset):
            graph = self.graph.to_dict()

        source_type: str | Unset = UNSET
        if not isinstance(self.source_type, Unset):
            source_type = self.source_type.value

        prompt_template_id: None | str | Unset
        if isinstance(self.prompt_template_id, Unset):
            prompt_template_id = UNSET
        elif isinstance(self.prompt_template_id, UUID):
            prompt_template_id = str(self.prompt_template_id)
        else:
            prompt_template_id = self.prompt_template_id

        prompt_version_id: None | str | Unset
        if isinstance(self.prompt_version_id, Unset):
            prompt_version_id = UNSET
        elif isinstance(self.prompt_version_id, UUID):
            prompt_version_id = str(self.prompt_version_id)
        else:
            prompt_version_id = self.prompt_version_id

        add_persona_automatically = self.add_persona_automatically

        personas: list[str] | Unset = UNSET
        if not isinstance(self.personas, Unset):
            personas = []
            for personas_item_data in self.personas:
                personas_item = str(personas_item_data)
                personas.append(personas_item)

        custom_columns: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.custom_columns, Unset):
            custom_columns = []
            for custom_columns_item_data in self.custom_columns:
                custom_columns_item = custom_columns_item_data.to_dict()
                custom_columns.append(custom_columns_item)

        agent_name = self.agent_name

        agent_prompt = self.agent_prompt

        voice_provider = self.voice_provider

        voice_name = self.voice_name

        model = self.model

        llm_temperature = self.llm_temperature

        initial_message = self.initial_message

        max_call_duration_in_minutes = self.max_call_duration_in_minutes

        interrupt_sensitivity = self.interrupt_sensitivity

        conversation_speed = self.conversation_speed

        finished_speaking_sensitivity = self.finished_speaking_sensitivity

        initial_message_delay = self.initial_message_delay

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if kind is not UNSET:
            field_dict["kind"] = kind
        if script_url is not UNSET:
            field_dict["script_url"] = script_url
        if agent_definition_id is not UNSET:
            field_dict["agent_definition_id"] = agent_definition_id
        if agent_definition_version_id is not UNSET:
            field_dict["agent_definition_version_id"] = agent_definition_version_id
        if custom_instruction is not UNSET:
            field_dict["custom_instruction"] = custom_instruction
        if no_of_rows is not UNSET:
            field_dict["no_of_rows"] = no_of_rows
        if generate_graph is not UNSET:
            field_dict["generate_graph"] = generate_graph
        if graph is not UNSET:
            field_dict["graph"] = graph
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if prompt_template_id is not UNSET:
            field_dict["prompt_template_id"] = prompt_template_id
        if prompt_version_id is not UNSET:
            field_dict["prompt_version_id"] = prompt_version_id
        if add_persona_automatically is not UNSET:
            field_dict["add_persona_automatically"] = add_persona_automatically
        if personas is not UNSET:
            field_dict["personas"] = personas
        if custom_columns is not UNSET:
            field_dict["custom_columns"] = custom_columns
        if agent_name is not UNSET:
            field_dict["agent_name"] = agent_name
        if agent_prompt is not UNSET:
            field_dict["agent_prompt"] = agent_prompt
        if voice_provider is not UNSET:
            field_dict["voice_provider"] = voice_provider
        if voice_name is not UNSET:
            field_dict["voice_name"] = voice_name
        if model is not UNSET:
            field_dict["model"] = model
        if llm_temperature is not UNSET:
            field_dict["llm_temperature"] = llm_temperature
        if initial_message is not UNSET:
            field_dict["initial_message"] = initial_message
        if max_call_duration_in_minutes is not UNSET:
            field_dict["max_call_duration_in_minutes"] = max_call_duration_in_minutes
        if interrupt_sensitivity is not UNSET:
            field_dict["interrupt_sensitivity"] = interrupt_sensitivity
        if conversation_speed is not UNSET:
            field_dict["conversation_speed"] = conversation_speed
        if finished_speaking_sensitivity is not UNSET:
            field_dict["finished_speaking_sensitivity"] = finished_speaking_sensitivity
        if initial_message_delay is not UNSET:
            field_dict["initial_message_delay"] = initial_message_delay

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_definition import ColumnDefinition
        from ..models.scenario_create_request_graph import ScenarioCreateRequestGraph

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description", UNSET)

        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        _kind = d.pop("kind", UNSET)
        kind: ScenarioCreateRequestKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = ScenarioCreateRequestKind(_kind)

        def _parse_script_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        script_url = _parse_script_url(d.pop("script_url", UNSET))

        _agent_definition_id = d.pop("agent_definition_id", UNSET)
        agent_definition_id: UUID | Unset
        if isinstance(_agent_definition_id, Unset):
            agent_definition_id = UNSET
        else:
            agent_definition_id = UUID(_agent_definition_id)

        def _parse_agent_definition_version_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_definition_version_id_type_0 = UUID(data)

                return agent_definition_version_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_definition_version_id = _parse_agent_definition_version_id(
            d.pop("agent_definition_version_id", UNSET)
        )

        custom_instruction = d.pop("custom_instruction", UNSET)

        no_of_rows = d.pop("no_of_rows", UNSET)

        generate_graph = d.pop("generate_graph", UNSET)

        _graph = d.pop("graph", UNSET)
        graph: ScenarioCreateRequestGraph | Unset
        if isinstance(_graph, Unset):
            graph = UNSET
        else:
            graph = ScenarioCreateRequestGraph.from_dict(_graph)

        _source_type = d.pop("source_type", UNSET)
        source_type: ScenarioCreateRequestSourceType | Unset
        if isinstance(_source_type, Unset):
            source_type = UNSET
        else:
            source_type = ScenarioCreateRequestSourceType(_source_type)

        def _parse_prompt_template_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_template_id_type_0 = UUID(data)

                return prompt_template_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_template_id = _parse_prompt_template_id(
            d.pop("prompt_template_id", UNSET)
        )

        def _parse_prompt_version_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_version_id_type_0 = UUID(data)

                return prompt_version_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_version_id = _parse_prompt_version_id(d.pop("prompt_version_id", UNSET))

        add_persona_automatically = d.pop("add_persona_automatically", UNSET)

        _personas = d.pop("personas", UNSET)
        personas: list[UUID] | Unset = UNSET
        if _personas is not UNSET:
            personas = []
            for personas_item_data in _personas:
                personas_item = UUID(personas_item_data)

                personas.append(personas_item)

        _custom_columns = d.pop("custom_columns", UNSET)
        custom_columns: list[ColumnDefinition] | Unset = UNSET
        if _custom_columns is not UNSET:
            custom_columns = []
            for custom_columns_item_data in _custom_columns:
                custom_columns_item = ColumnDefinition.from_dict(
                    custom_columns_item_data
                )

                custom_columns.append(custom_columns_item)

        agent_name = d.pop("agent_name", UNSET)

        agent_prompt = d.pop("agent_prompt", UNSET)

        voice_provider = d.pop("voice_provider", UNSET)

        voice_name = d.pop("voice_name", UNSET)

        model = d.pop("model", UNSET)

        llm_temperature = d.pop("llm_temperature", UNSET)

        initial_message = d.pop("initial_message", UNSET)

        max_call_duration_in_minutes = d.pop("max_call_duration_in_minutes", UNSET)

        interrupt_sensitivity = d.pop("interrupt_sensitivity", UNSET)

        conversation_speed = d.pop("conversation_speed", UNSET)

        finished_speaking_sensitivity = d.pop("finished_speaking_sensitivity", UNSET)

        initial_message_delay = d.pop("initial_message_delay", UNSET)

        scenario_create_request = cls(
            name=name,
            description=description,
            dataset_id=dataset_id,
            kind=kind,
            script_url=script_url,
            agent_definition_id=agent_definition_id,
            agent_definition_version_id=agent_definition_version_id,
            custom_instruction=custom_instruction,
            no_of_rows=no_of_rows,
            generate_graph=generate_graph,
            graph=graph,
            source_type=source_type,
            prompt_template_id=prompt_template_id,
            prompt_version_id=prompt_version_id,
            add_persona_automatically=add_persona_automatically,
            personas=personas,
            custom_columns=custom_columns,
            agent_name=agent_name,
            agent_prompt=agent_prompt,
            voice_provider=voice_provider,
            voice_name=voice_name,
            model=model,
            llm_temperature=llm_temperature,
            initial_message=initial_message,
            max_call_duration_in_minutes=max_call_duration_in_minutes,
            interrupt_sensitivity=interrupt_sensitivity,
            conversation_speed=conversation_speed,
            finished_speaking_sensitivity=finished_speaking_sensitivity,
            initial_message_delay=initial_message_delay,
        )

        scenario_create_request.additional_properties = d
        return scenario_create_request

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
