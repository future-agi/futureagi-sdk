from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.external_run_binding_binding_config_type_4_type_0 import (
        ExternalRunBindingBindingConfigType4Type0,
    )
    from ..models.external_run_binding_choice_scores_type_4_type_0 import (
        ExternalRunBindingChoiceScoresType4Type0,
    )
    from ..models.external_run_binding_config_snapshot_type_4_type_0 import (
        ExternalRunBindingConfigSnapshotType4Type0,
    )
    from ..models.external_run_binding_prompt_messages_type_4_type_0 import (
        ExternalRunBindingPromptMessagesType4Type0,
    )


T = TypeVar("T", bound="ExternalRunBinding")


@_attrs_define
class ExternalRunBinding:
    """
    Attributes:
        metric_id (UUID):
        evaluator_version_id (UUID):
        template_id (UUID):
        version_number (int):
        binding_config (bool | ExternalRunBindingBindingConfigType4Type0 | float | list[Any] | None | str): Any valid
            JSON value.
        binding_model (None | str):
        prompt_messages (bool | ExternalRunBindingPromptMessagesType4Type0 | float | list[Any] | None | str): Any valid
            JSON value.
        config_snapshot (bool | ExternalRunBindingConfigSnapshotType4Type0 | float | list[Any] | None | str): Any valid
            JSON value.
        criteria (None | str):
        model (None | str):
        output_type_normalized (None | str):
        pass_threshold (float | None):
        choice_scores (bool | ExternalRunBindingChoiceScoresType4Type0 | float | list[Any] | None | str): Any valid JSON
            value.
    """

    metric_id: UUID
    evaluator_version_id: UUID
    template_id: UUID
    version_number: int
    binding_config: (
        bool
        | ExternalRunBindingBindingConfigType4Type0
        | float
        | list[Any]
        | None
        | str
    )
    binding_model: None | str
    prompt_messages: (
        bool
        | ExternalRunBindingPromptMessagesType4Type0
        | float
        | list[Any]
        | None
        | str
    )
    config_snapshot: (
        bool
        | ExternalRunBindingConfigSnapshotType4Type0
        | float
        | list[Any]
        | None
        | str
    )
    criteria: None | str
    model: None | str
    output_type_normalized: None | str
    pass_threshold: float | None
    choice_scores: (
        bool | ExternalRunBindingChoiceScoresType4Type0 | float | list[Any] | None | str
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.external_run_binding_binding_config_type_4_type_0 import (
            ExternalRunBindingBindingConfigType4Type0,
        )
        from ..models.external_run_binding_choice_scores_type_4_type_0 import (
            ExternalRunBindingChoiceScoresType4Type0,
        )
        from ..models.external_run_binding_config_snapshot_type_4_type_0 import (
            ExternalRunBindingConfigSnapshotType4Type0,
        )
        from ..models.external_run_binding_prompt_messages_type_4_type_0 import (
            ExternalRunBindingPromptMessagesType4Type0,
        )

        metric_id = str(self.metric_id)

        evaluator_version_id = str(self.evaluator_version_id)

        template_id = str(self.template_id)

        version_number = self.version_number

        binding_config: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.binding_config, list):
            binding_config = self.binding_config

        elif isinstance(self.binding_config, ExternalRunBindingBindingConfigType4Type0):
            binding_config = self.binding_config.to_dict()
        else:
            binding_config = self.binding_config

        binding_model: None | str
        binding_model = self.binding_model

        prompt_messages: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.prompt_messages, list):
            prompt_messages = self.prompt_messages

        elif isinstance(
            self.prompt_messages, ExternalRunBindingPromptMessagesType4Type0
        ):
            prompt_messages = self.prompt_messages.to_dict()
        else:
            prompt_messages = self.prompt_messages

        config_snapshot: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.config_snapshot, list):
            config_snapshot = self.config_snapshot

        elif isinstance(
            self.config_snapshot, ExternalRunBindingConfigSnapshotType4Type0
        ):
            config_snapshot = self.config_snapshot.to_dict()
        else:
            config_snapshot = self.config_snapshot

        criteria: None | str
        criteria = self.criteria

        model: None | str
        model = self.model

        output_type_normalized: None | str
        output_type_normalized = self.output_type_normalized

        pass_threshold: float | None
        pass_threshold = self.pass_threshold

        choice_scores: bool | dict[str, Any] | float | list[Any] | None | str
        if isinstance(self.choice_scores, list):
            choice_scores = self.choice_scores

        elif isinstance(self.choice_scores, ExternalRunBindingChoiceScoresType4Type0):
            choice_scores = self.choice_scores.to_dict()
        else:
            choice_scores = self.choice_scores

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metric_id": metric_id,
                "evaluator_version_id": evaluator_version_id,
                "template_id": template_id,
                "version_number": version_number,
                "binding_config": binding_config,
                "binding_model": binding_model,
                "prompt_messages": prompt_messages,
                "config_snapshot": config_snapshot,
                "criteria": criteria,
                "model": model,
                "output_type_normalized": output_type_normalized,
                "pass_threshold": pass_threshold,
                "choice_scores": choice_scores,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_binding_binding_config_type_4_type_0 import (
            ExternalRunBindingBindingConfigType4Type0,
        )
        from ..models.external_run_binding_choice_scores_type_4_type_0 import (
            ExternalRunBindingChoiceScoresType4Type0,
        )
        from ..models.external_run_binding_config_snapshot_type_4_type_0 import (
            ExternalRunBindingConfigSnapshotType4Type0,
        )
        from ..models.external_run_binding_prompt_messages_type_4_type_0 import (
            ExternalRunBindingPromptMessagesType4Type0,
        )

        d = dict(src_dict)
        metric_id = UUID(d.pop("metric_id"))

        evaluator_version_id = UUID(d.pop("evaluator_version_id"))

        template_id = UUID(d.pop("template_id"))

        version_number = d.pop("version_number")

        def _parse_binding_config(
            data: object,
        ) -> (
            bool
            | ExternalRunBindingBindingConfigType4Type0
            | float
            | list[Any]
            | None
            | str
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                binding_config_type_3 = cast(list[Any], data)

                return binding_config_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                binding_config_type_4_type_0 = (
                    ExternalRunBindingBindingConfigType4Type0.from_dict(data)
                )

                return binding_config_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunBindingBindingConfigType4Type0
                | float
                | list[Any]
                | None
                | str,
                data,
            )

        binding_config = _parse_binding_config(d.pop("binding_config"))

        def _parse_binding_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        binding_model = _parse_binding_model(d.pop("binding_model"))

        def _parse_prompt_messages(
            data: object,
        ) -> (
            bool
            | ExternalRunBindingPromptMessagesType4Type0
            | float
            | list[Any]
            | None
            | str
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                prompt_messages_type_3 = cast(list[Any], data)

                return prompt_messages_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                prompt_messages_type_4_type_0 = (
                    ExternalRunBindingPromptMessagesType4Type0.from_dict(data)
                )

                return prompt_messages_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunBindingPromptMessagesType4Type0
                | float
                | list[Any]
                | None
                | str,
                data,
            )

        prompt_messages = _parse_prompt_messages(d.pop("prompt_messages"))

        def _parse_config_snapshot(
            data: object,
        ) -> (
            bool
            | ExternalRunBindingConfigSnapshotType4Type0
            | float
            | list[Any]
            | None
            | str
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                config_snapshot_type_3 = cast(list[Any], data)

                return config_snapshot_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                config_snapshot_type_4_type_0 = (
                    ExternalRunBindingConfigSnapshotType4Type0.from_dict(data)
                )

                return config_snapshot_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunBindingConfigSnapshotType4Type0
                | float
                | list[Any]
                | None
                | str,
                data,
            )

        config_snapshot = _parse_config_snapshot(d.pop("config_snapshot"))

        def _parse_criteria(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        criteria = _parse_criteria(d.pop("criteria"))

        def _parse_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model = _parse_model(d.pop("model"))

        def _parse_output_type_normalized(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        output_type_normalized = _parse_output_type_normalized(
            d.pop("output_type_normalized")
        )

        def _parse_pass_threshold(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        pass_threshold = _parse_pass_threshold(d.pop("pass_threshold"))

        def _parse_choice_scores(
            data: object,
        ) -> (
            bool
            | ExternalRunBindingChoiceScoresType4Type0
            | float
            | list[Any]
            | None
            | str
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                choice_scores_type_3 = cast(list[Any], data)

                return choice_scores_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                choice_scores_type_4_type_0 = (
                    ExternalRunBindingChoiceScoresType4Type0.from_dict(data)
                )

                return choice_scores_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | ExternalRunBindingChoiceScoresType4Type0
                | float
                | list[Any]
                | None
                | str,
                data,
            )

        choice_scores = _parse_choice_scores(d.pop("choice_scores"))

        external_run_binding = cls(
            metric_id=metric_id,
            evaluator_version_id=evaluator_version_id,
            template_id=template_id,
            version_number=version_number,
            binding_config=binding_config,
            binding_model=binding_model,
            prompt_messages=prompt_messages,
            config_snapshot=config_snapshot,
            criteria=criteria,
            model=model,
            output_type_normalized=output_type_normalized,
            pass_threshold=pass_threshold,
            choice_scores=choice_scores,
        )

        external_run_binding.additional_properties = d
        return external_run_binding

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
