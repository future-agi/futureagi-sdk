from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.prompt_history_execution_evaluation_configs import (
        PromptHistoryExecutionEvaluationConfigs,
    )
    from ..models.prompt_history_execution_evaluation_results import (
        PromptHistoryExecutionEvaluationResults,
    )
    from ..models.prompt_history_execution_metadata import (
        PromptHistoryExecutionMetadata,
    )
    from ..models.prompt_history_execution_output import PromptHistoryExecutionOutput
    from ..models.prompt_history_execution_placeholders import (
        PromptHistoryExecutionPlaceholders,
    )


T = TypeVar("T", bound="PromptHistoryExecution")


@_attrs_define
class PromptHistoryExecution:
    """
    Attributes:
        template_version (str):
        id (UUID | Unset):
        output (PromptHistoryExecutionOutput | Unset):
        prompt_config_snapshot (str | Unset):
        template_name (str | Unset):
        original_template (None | Unset | UUID):
        metadata (PromptHistoryExecutionMetadata | Unset):
        variable_names (str | Unset):
        evaluation_results (PromptHistoryExecutionEvaluationResults | Unset):
        evaluation_configs (PromptHistoryExecutionEvaluationConfigs | Unset):
        created_at (datetime.datetime | Unset):
        is_default (bool | Unset):
        commit_message (None | str | Unset):
        updated_at (datetime.datetime | Unset):
        is_draft (bool | Unset):
        labels (str | Unset):
        placeholders (PromptHistoryExecutionPlaceholders | Unset):
        prompt_base_template (None | Unset | UUID):
    """

    template_version: str
    id: UUID | Unset = UNSET
    output: PromptHistoryExecutionOutput | Unset = UNSET
    prompt_config_snapshot: str | Unset = UNSET
    template_name: str | Unset = UNSET
    original_template: None | Unset | UUID = UNSET
    metadata: PromptHistoryExecutionMetadata | Unset = UNSET
    variable_names: str | Unset = UNSET
    evaluation_results: PromptHistoryExecutionEvaluationResults | Unset = UNSET
    evaluation_configs: PromptHistoryExecutionEvaluationConfigs | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    is_default: bool | Unset = UNSET
    commit_message: None | str | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    is_draft: bool | Unset = UNSET
    labels: str | Unset = UNSET
    placeholders: PromptHistoryExecutionPlaceholders | Unset = UNSET
    prompt_base_template: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_version = self.template_version

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        prompt_config_snapshot = self.prompt_config_snapshot

        template_name = self.template_name

        original_template: None | str | Unset
        if isinstance(self.original_template, Unset):
            original_template = UNSET
        elif isinstance(self.original_template, UUID):
            original_template = str(self.original_template)
        else:
            original_template = self.original_template

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        variable_names = self.variable_names

        evaluation_results: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evaluation_results, Unset):
            evaluation_results = self.evaluation_results.to_dict()

        evaluation_configs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evaluation_configs, Unset):
            evaluation_configs = self.evaluation_configs.to_dict()

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        is_default = self.is_default

        commit_message: None | str | Unset
        if isinstance(self.commit_message, Unset):
            commit_message = UNSET
        else:
            commit_message = self.commit_message

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        is_draft = self.is_draft

        labels = self.labels

        placeholders: dict[str, Any] | Unset = UNSET
        if not isinstance(self.placeholders, Unset):
            placeholders = self.placeholders.to_dict()

        prompt_base_template: None | str | Unset
        if isinstance(self.prompt_base_template, Unset):
            prompt_base_template = UNSET
        elif isinstance(self.prompt_base_template, UUID):
            prompt_base_template = str(self.prompt_base_template)
        else:
            prompt_base_template = self.prompt_base_template

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_version": template_version,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if output is not UNSET:
            field_dict["output"] = output
        if prompt_config_snapshot is not UNSET:
            field_dict["prompt_config_snapshot"] = prompt_config_snapshot
        if template_name is not UNSET:
            field_dict["template_name"] = template_name
        if original_template is not UNSET:
            field_dict["original_template"] = original_template
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if variable_names is not UNSET:
            field_dict["variable_names"] = variable_names
        if evaluation_results is not UNSET:
            field_dict["evaluation_results"] = evaluation_results
        if evaluation_configs is not UNSET:
            field_dict["evaluation_configs"] = evaluation_configs
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if is_default is not UNSET:
            field_dict["is_default"] = is_default
        if commit_message is not UNSET:
            field_dict["commit_message"] = commit_message
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if is_draft is not UNSET:
            field_dict["is_draft"] = is_draft
        if labels is not UNSET:
            field_dict["labels"] = labels
        if placeholders is not UNSET:
            field_dict["placeholders"] = placeholders
        if prompt_base_template is not UNSET:
            field_dict["prompt_base_template"] = prompt_base_template

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_history_execution_evaluation_configs import (
            PromptHistoryExecutionEvaluationConfigs,
        )
        from ..models.prompt_history_execution_evaluation_results import (
            PromptHistoryExecutionEvaluationResults,
        )
        from ..models.prompt_history_execution_metadata import (
            PromptHistoryExecutionMetadata,
        )
        from ..models.prompt_history_execution_output import (
            PromptHistoryExecutionOutput,
        )
        from ..models.prompt_history_execution_placeholders import (
            PromptHistoryExecutionPlaceholders,
        )

        d = dict(src_dict)
        template_version = d.pop("template_version")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _output = d.pop("output", UNSET)
        output: PromptHistoryExecutionOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = PromptHistoryExecutionOutput.from_dict(_output)

        prompt_config_snapshot = d.pop("prompt_config_snapshot", UNSET)

        template_name = d.pop("template_name", UNSET)

        def _parse_original_template(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                original_template_type_0 = UUID(data)

                return original_template_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        original_template = _parse_original_template(d.pop("original_template", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: PromptHistoryExecutionMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = PromptHistoryExecutionMetadata.from_dict(_metadata)

        variable_names = d.pop("variable_names", UNSET)

        _evaluation_results = d.pop("evaluation_results", UNSET)
        evaluation_results: PromptHistoryExecutionEvaluationResults | Unset
        if isinstance(_evaluation_results, Unset):
            evaluation_results = UNSET
        else:
            evaluation_results = PromptHistoryExecutionEvaluationResults.from_dict(
                _evaluation_results
            )

        _evaluation_configs = d.pop("evaluation_configs", UNSET)
        evaluation_configs: PromptHistoryExecutionEvaluationConfigs | Unset
        if isinstance(_evaluation_configs, Unset):
            evaluation_configs = UNSET
        else:
            evaluation_configs = PromptHistoryExecutionEvaluationConfigs.from_dict(
                _evaluation_configs
            )

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        is_default = d.pop("is_default", UNSET)

        def _parse_commit_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        commit_message = _parse_commit_message(d.pop("commit_message", UNSET))

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        is_draft = d.pop("is_draft", UNSET)

        labels = d.pop("labels", UNSET)

        _placeholders = d.pop("placeholders", UNSET)
        placeholders: PromptHistoryExecutionPlaceholders | Unset
        if isinstance(_placeholders, Unset):
            placeholders = UNSET
        else:
            placeholders = PromptHistoryExecutionPlaceholders.from_dict(_placeholders)

        def _parse_prompt_base_template(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_base_template_type_0 = UUID(data)

                return prompt_base_template_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_base_template = _parse_prompt_base_template(
            d.pop("prompt_base_template", UNSET)
        )

        prompt_history_execution = cls(
            template_version=template_version,
            id=id,
            output=output,
            prompt_config_snapshot=prompt_config_snapshot,
            template_name=template_name,
            original_template=original_template,
            metadata=metadata,
            variable_names=variable_names,
            evaluation_results=evaluation_results,
            evaluation_configs=evaluation_configs,
            created_at=created_at,
            is_default=is_default,
            commit_message=commit_message,
            updated_at=updated_at,
            is_draft=is_draft,
            labels=labels,
            placeholders=placeholders,
            prompt_base_template=prompt_base_template,
        )

        prompt_history_execution.additional_properties = d
        return prompt_history_execution

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
