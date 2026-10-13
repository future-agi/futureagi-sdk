from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_template_create_v2_request_code_language import (
    EvalTemplateCreateV2RequestCodeLanguage,
)
from ..models.eval_template_create_v2_request_eval_type import (
    EvalTemplateCreateV2RequestEvalType,
)
from ..models.eval_template_create_v2_request_mode import (
    EvalTemplateCreateV2RequestMode,
)
from ..models.eval_template_create_v2_request_output_type import (
    EvalTemplateCreateV2RequestOutputType,
)
from ..models.eval_template_create_v2_request_template_format import (
    EvalTemplateCreateV2RequestTemplateFormat,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_template_create_v2_request_choice_scores import (
        EvalTemplateCreateV2RequestChoiceScores,
    )
    from ..models.eval_template_create_v2_request_data_injection import (
        EvalTemplateCreateV2RequestDataInjection,
    )
    from ..models.eval_template_create_v2_request_few_shot_examples_type_0_item import (
        EvalTemplateCreateV2RequestFewShotExamplesType0Item,
    )
    from ..models.eval_template_create_v2_request_messages_type_0_item import (
        EvalTemplateCreateV2RequestMessagesType0Item,
    )
    from ..models.eval_template_create_v2_request_summary import (
        EvalTemplateCreateV2RequestSummary,
    )
    from ..models.eval_template_create_v2_request_tools import (
        EvalTemplateCreateV2RequestTools,
    )


T = TypeVar("T", bound="EvalTemplateCreateV2Request")


@_attrs_define
class EvalTemplateCreateV2Request:
    """
    Attributes:
        name (str | Unset):
        is_draft (bool | Unset):  Default: False.
        eval_type (EvalTemplateCreateV2RequestEvalType | Unset):  Default: EvalTemplateCreateV2RequestEvalType.LLM.
        instructions (str | Unset):
        model (str | Unset):  Default: 'turing_large'.
        output_type (EvalTemplateCreateV2RequestOutputType | Unset):  Default:
            EvalTemplateCreateV2RequestOutputType.PASS_FAIL.
        pass_threshold (float | Unset):
        choice_scores (EvalTemplateCreateV2RequestChoiceScores | Unset):
        description (None | str | Unset):
        tags (list[str] | Unset):
        check_internet (bool | Unset):  Default: False.
        code (None | str | Unset):
        code_language (EvalTemplateCreateV2RequestCodeLanguage | Unset):
        messages (list[EvalTemplateCreateV2RequestMessagesType0Item] | None | Unset):
        few_shot_examples (list[EvalTemplateCreateV2RequestFewShotExamplesType0Item] | None | Unset):
        mode (EvalTemplateCreateV2RequestMode | Unset):
        tools (EvalTemplateCreateV2RequestTools | Unset):
        knowledge_bases (list[str] | None | Unset):
        data_injection (EvalTemplateCreateV2RequestDataInjection | Unset):
        summary (EvalTemplateCreateV2RequestSummary | Unset):
        error_localizer_enabled (bool | Unset):  Default: False.
        template_format (EvalTemplateCreateV2RequestTemplateFormat | Unset):  Default:
            EvalTemplateCreateV2RequestTemplateFormat.MUSTACHE.
    """

    name: str | Unset = UNSET
    is_draft: bool | Unset = False
    eval_type: EvalTemplateCreateV2RequestEvalType | Unset = (
        EvalTemplateCreateV2RequestEvalType.LLM
    )
    instructions: str | Unset = UNSET
    model: str | Unset = "turing_large"
    output_type: EvalTemplateCreateV2RequestOutputType | Unset = (
        EvalTemplateCreateV2RequestOutputType.PASS_FAIL
    )
    pass_threshold: float | Unset = UNSET
    choice_scores: EvalTemplateCreateV2RequestChoiceScores | Unset = UNSET
    description: None | str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    check_internet: bool | Unset = False
    code: None | str | Unset = UNSET
    code_language: EvalTemplateCreateV2RequestCodeLanguage | Unset = UNSET
    messages: list[EvalTemplateCreateV2RequestMessagesType0Item] | None | Unset = UNSET
    few_shot_examples: (
        list[EvalTemplateCreateV2RequestFewShotExamplesType0Item] | None | Unset
    ) = UNSET
    mode: EvalTemplateCreateV2RequestMode | Unset = UNSET
    tools: EvalTemplateCreateV2RequestTools | Unset = UNSET
    knowledge_bases: list[str] | None | Unset = UNSET
    data_injection: EvalTemplateCreateV2RequestDataInjection | Unset = UNSET
    summary: EvalTemplateCreateV2RequestSummary | Unset = UNSET
    error_localizer_enabled: bool | Unset = False
    template_format: EvalTemplateCreateV2RequestTemplateFormat | Unset = (
        EvalTemplateCreateV2RequestTemplateFormat.MUSTACHE
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        is_draft = self.is_draft

        eval_type: str | Unset = UNSET
        if not isinstance(self.eval_type, Unset):
            eval_type = self.eval_type.value

        instructions = self.instructions

        model = self.model

        output_type: str | Unset = UNSET
        if not isinstance(self.output_type, Unset):
            output_type = self.output_type.value

        pass_threshold = self.pass_threshold

        choice_scores: dict[str, Any] | Unset = UNSET
        if not isinstance(self.choice_scores, Unset):
            choice_scores = self.choice_scores.to_dict()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        check_internet = self.check_internet

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        code_language: str | Unset = UNSET
        if not isinstance(self.code_language, Unset):
            code_language = self.code_language.value

        messages: list[dict[str, Any]] | None | Unset
        if isinstance(self.messages, Unset):
            messages = UNSET
        elif isinstance(self.messages, list):
            messages = []
            for messages_type_0_item_data in self.messages:
                messages_type_0_item = messages_type_0_item_data.to_dict()
                messages.append(messages_type_0_item)

        else:
            messages = self.messages

        few_shot_examples: list[dict[str, Any]] | None | Unset
        if isinstance(self.few_shot_examples, Unset):
            few_shot_examples = UNSET
        elif isinstance(self.few_shot_examples, list):
            few_shot_examples = []
            for few_shot_examples_type_0_item_data in self.few_shot_examples:
                few_shot_examples_type_0_item = (
                    few_shot_examples_type_0_item_data.to_dict()
                )
                few_shot_examples.append(few_shot_examples_type_0_item)

        else:
            few_shot_examples = self.few_shot_examples

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        tools: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tools, Unset):
            tools = self.tools.to_dict()

        knowledge_bases: list[str] | None | Unset
        if isinstance(self.knowledge_bases, Unset):
            knowledge_bases = UNSET
        elif isinstance(self.knowledge_bases, list):
            knowledge_bases = self.knowledge_bases

        else:
            knowledge_bases = self.knowledge_bases

        data_injection: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data_injection, Unset):
            data_injection = self.data_injection.to_dict()

        summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.summary, Unset):
            summary = self.summary.to_dict()

        error_localizer_enabled = self.error_localizer_enabled

        template_format: str | Unset = UNSET
        if not isinstance(self.template_format, Unset):
            template_format = self.template_format.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if is_draft is not UNSET:
            field_dict["is_draft"] = is_draft
        if eval_type is not UNSET:
            field_dict["eval_type"] = eval_type
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if model is not UNSET:
            field_dict["model"] = model
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if pass_threshold is not UNSET:
            field_dict["pass_threshold"] = pass_threshold
        if choice_scores is not UNSET:
            field_dict["choice_scores"] = choice_scores
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if check_internet is not UNSET:
            field_dict["check_internet"] = check_internet
        if code is not UNSET:
            field_dict["code"] = code
        if code_language is not UNSET:
            field_dict["code_language"] = code_language
        if messages is not UNSET:
            field_dict["messages"] = messages
        if few_shot_examples is not UNSET:
            field_dict["few_shot_examples"] = few_shot_examples
        if mode is not UNSET:
            field_dict["mode"] = mode
        if tools is not UNSET:
            field_dict["tools"] = tools
        if knowledge_bases is not UNSET:
            field_dict["knowledge_bases"] = knowledge_bases
        if data_injection is not UNSET:
            field_dict["data_injection"] = data_injection
        if summary is not UNSET:
            field_dict["summary"] = summary
        if error_localizer_enabled is not UNSET:
            field_dict["error_localizer_enabled"] = error_localizer_enabled
        if template_format is not UNSET:
            field_dict["template_format"] = template_format

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_create_v2_request_choice_scores import (
            EvalTemplateCreateV2RequestChoiceScores,
        )
        from ..models.eval_template_create_v2_request_data_injection import (
            EvalTemplateCreateV2RequestDataInjection,
        )
        from ..models.eval_template_create_v2_request_few_shot_examples_type_0_item import (
            EvalTemplateCreateV2RequestFewShotExamplesType0Item,
        )
        from ..models.eval_template_create_v2_request_messages_type_0_item import (
            EvalTemplateCreateV2RequestMessagesType0Item,
        )
        from ..models.eval_template_create_v2_request_summary import (
            EvalTemplateCreateV2RequestSummary,
        )
        from ..models.eval_template_create_v2_request_tools import (
            EvalTemplateCreateV2RequestTools,
        )

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        is_draft = d.pop("is_draft", UNSET)

        _eval_type = d.pop("eval_type", UNSET)
        eval_type: EvalTemplateCreateV2RequestEvalType | Unset
        if isinstance(_eval_type, Unset):
            eval_type = UNSET
        else:
            eval_type = EvalTemplateCreateV2RequestEvalType(_eval_type)

        instructions = d.pop("instructions", UNSET)

        model = d.pop("model", UNSET)

        _output_type = d.pop("output_type", UNSET)
        output_type: EvalTemplateCreateV2RequestOutputType | Unset
        if isinstance(_output_type, Unset):
            output_type = UNSET
        else:
            output_type = EvalTemplateCreateV2RequestOutputType(_output_type)

        pass_threshold = d.pop("pass_threshold", UNSET)

        _choice_scores = d.pop("choice_scores", UNSET)
        choice_scores: EvalTemplateCreateV2RequestChoiceScores | Unset
        if isinstance(_choice_scores, Unset):
            choice_scores = UNSET
        else:
            choice_scores = EvalTemplateCreateV2RequestChoiceScores.from_dict(
                _choice_scores
            )

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        check_internet = d.pop("check_internet", UNSET)

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        _code_language = d.pop("code_language", UNSET)
        code_language: EvalTemplateCreateV2RequestCodeLanguage | Unset
        if isinstance(_code_language, Unset):
            code_language = UNSET
        else:
            code_language = EvalTemplateCreateV2RequestCodeLanguage(_code_language)

        def _parse_messages(
            data: object,
        ) -> list[EvalTemplateCreateV2RequestMessagesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                messages_type_0 = []
                _messages_type_0 = data
                for messages_type_0_item_data in _messages_type_0:
                    messages_type_0_item = (
                        EvalTemplateCreateV2RequestMessagesType0Item.from_dict(
                            messages_type_0_item_data
                        )
                    )

                    messages_type_0.append(messages_type_0_item)

                return messages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[EvalTemplateCreateV2RequestMessagesType0Item] | None | Unset, data
            )

        messages = _parse_messages(d.pop("messages", UNSET))

        def _parse_few_shot_examples(
            data: object,
        ) -> list[EvalTemplateCreateV2RequestFewShotExamplesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                few_shot_examples_type_0 = []
                _few_shot_examples_type_0 = data
                for few_shot_examples_type_0_item_data in _few_shot_examples_type_0:
                    few_shot_examples_type_0_item = (
                        EvalTemplateCreateV2RequestFewShotExamplesType0Item.from_dict(
                            few_shot_examples_type_0_item_data
                        )
                    )

                    few_shot_examples_type_0.append(few_shot_examples_type_0_item)

                return few_shot_examples_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[EvalTemplateCreateV2RequestFewShotExamplesType0Item]
                | None
                | Unset,
                data,
            )

        few_shot_examples = _parse_few_shot_examples(d.pop("few_shot_examples", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: EvalTemplateCreateV2RequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = EvalTemplateCreateV2RequestMode(_mode)

        _tools = d.pop("tools", UNSET)
        tools: EvalTemplateCreateV2RequestTools | Unset
        if isinstance(_tools, Unset):
            tools = UNSET
        else:
            tools = EvalTemplateCreateV2RequestTools.from_dict(_tools)

        def _parse_knowledge_bases(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                knowledge_bases_type_0 = cast(list[str], data)

                return knowledge_bases_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        knowledge_bases = _parse_knowledge_bases(d.pop("knowledge_bases", UNSET))

        _data_injection = d.pop("data_injection", UNSET)
        data_injection: EvalTemplateCreateV2RequestDataInjection | Unset
        if isinstance(_data_injection, Unset):
            data_injection = UNSET
        else:
            data_injection = EvalTemplateCreateV2RequestDataInjection.from_dict(
                _data_injection
            )

        _summary = d.pop("summary", UNSET)
        summary: EvalTemplateCreateV2RequestSummary | Unset
        if isinstance(_summary, Unset):
            summary = UNSET
        else:
            summary = EvalTemplateCreateV2RequestSummary.from_dict(_summary)

        error_localizer_enabled = d.pop("error_localizer_enabled", UNSET)

        _template_format = d.pop("template_format", UNSET)
        template_format: EvalTemplateCreateV2RequestTemplateFormat | Unset
        if isinstance(_template_format, Unset):
            template_format = UNSET
        else:
            template_format = EvalTemplateCreateV2RequestTemplateFormat(
                _template_format
            )

        eval_template_create_v2_request = cls(
            name=name,
            is_draft=is_draft,
            eval_type=eval_type,
            instructions=instructions,
            model=model,
            output_type=output_type,
            pass_threshold=pass_threshold,
            choice_scores=choice_scores,
            description=description,
            tags=tags,
            check_internet=check_internet,
            code=code,
            code_language=code_language,
            messages=messages,
            few_shot_examples=few_shot_examples,
            mode=mode,
            tools=tools,
            knowledge_bases=knowledge_bases,
            data_injection=data_injection,
            summary=summary,
            error_localizer_enabled=error_localizer_enabled,
            template_format=template_format,
        )

        eval_template_create_v2_request.additional_properties = d
        return eval_template_create_v2_request

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
