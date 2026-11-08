from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.rca_trail_step_args import RcaTrailStepArgs
    from ..models.rca_trail_step_result import RcaTrailStepResult


T = TypeVar("T", bound="RcaTrailStep")


@_attrs_define
class RcaTrailStep:
    """
    Attributes:
        type_ (str):
        text (None | str | Unset):
        call_id (None | str | Unset):
        tool (None | str | Unset):
        args (RcaTrailStepArgs | Unset):
        result (RcaTrailStepResult | Unset):
        synthesis (None | str | Unset):
        fix (None | str | Unset):
        confidence (None | str | Unset):
    """

    type_: str
    text: None | str | Unset = UNSET
    call_id: None | str | Unset = UNSET
    tool: None | str | Unset = UNSET
    args: RcaTrailStepArgs | Unset = UNSET
    result: RcaTrailStepResult | Unset = UNSET
    synthesis: None | str | Unset = UNSET
    fix: None | str | Unset = UNSET
    confidence: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        text: None | str | Unset
        if isinstance(self.text, Unset):
            text = UNSET
        else:
            text = self.text

        call_id: None | str | Unset
        if isinstance(self.call_id, Unset):
            call_id = UNSET
        else:
            call_id = self.call_id

        tool: None | str | Unset
        if isinstance(self.tool, Unset):
            tool = UNSET
        else:
            tool = self.tool

        args: dict[str, Any] | Unset = UNSET
        if not isinstance(self.args, Unset):
            args = self.args.to_dict()

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        synthesis: None | str | Unset
        if isinstance(self.synthesis, Unset):
            synthesis = UNSET
        else:
            synthesis = self.synthesis

        fix: None | str | Unset
        if isinstance(self.fix, Unset):
            fix = UNSET
        else:
            fix = self.fix

        confidence: None | str | Unset
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if text is not UNSET:
            field_dict["text"] = text
        if call_id is not UNSET:
            field_dict["call_id"] = call_id
        if tool is not UNSET:
            field_dict["tool"] = tool
        if args is not UNSET:
            field_dict["args"] = args
        if result is not UNSET:
            field_dict["result"] = result
        if synthesis is not UNSET:
            field_dict["synthesis"] = synthesis
        if fix is not UNSET:
            field_dict["fix"] = fix
        if confidence is not UNSET:
            field_dict["confidence"] = confidence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.rca_trail_step_args import RcaTrailStepArgs
        from ..models.rca_trail_step_result import RcaTrailStepResult

        d = dict(src_dict)
        type_ = d.pop("type")

        def _parse_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        text = _parse_text(d.pop("text", UNSET))

        def _parse_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_id = _parse_call_id(d.pop("call_id", UNSET))

        def _parse_tool(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tool = _parse_tool(d.pop("tool", UNSET))

        _args = d.pop("args", UNSET)
        args: RcaTrailStepArgs | Unset
        if isinstance(_args, Unset):
            args = UNSET
        else:
            args = RcaTrailStepArgs.from_dict(_args)

        _result = d.pop("result", UNSET)
        result: RcaTrailStepResult | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = RcaTrailStepResult.from_dict(_result)

        def _parse_synthesis(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        synthesis = _parse_synthesis(d.pop("synthesis", UNSET))

        def _parse_fix(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        fix = _parse_fix(d.pop("fix", UNSET))

        def _parse_confidence(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        rca_trail_step = cls(
            type_=type_,
            text=text,
            call_id=call_id,
            tool=tool,
            args=args,
            result=result,
            synthesis=synthesis,
            fix=fix,
            confidence=confidence,
        )

        rca_trail_step.additional_properties = d
        return rca_trail_step

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
