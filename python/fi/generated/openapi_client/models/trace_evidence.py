from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_evidence_fail_reel_item import TraceEvidenceFailReelItem
    from ..models.trace_evidence_pass_reel_item import TraceEvidencePassReelItem


T = TypeVar("T", bound="TraceEvidence")


@_attrs_define
class TraceEvidence:
    """
    Attributes:
        input_ (None | str):
        output (None | str):
        fail_reel (list[TraceEvidenceFailReelItem]):
        pass_reel (list[TraceEvidencePassReelItem]):
    """

    input_: None | str
    output: None | str
    fail_reel: list[TraceEvidenceFailReelItem]
    pass_reel: list[TraceEvidencePassReelItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_: None | str
        input_ = self.input_

        output: None | str
        output = self.output

        fail_reel = []
        for fail_reel_item_data in self.fail_reel:
            fail_reel_item = fail_reel_item_data.to_dict()
            fail_reel.append(fail_reel_item)

        pass_reel = []
        for pass_reel_item_data in self.pass_reel:
            pass_reel_item = pass_reel_item_data.to_dict()
            pass_reel.append(pass_reel_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input": input_,
                "output": output,
                "fail_reel": fail_reel,
                "pass_reel": pass_reel,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_evidence_fail_reel_item import TraceEvidenceFailReelItem
        from ..models.trace_evidence_pass_reel_item import TraceEvidencePassReelItem

        d = dict(src_dict)

        def _parse_input_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        input_ = _parse_input_(d.pop("input"))

        def _parse_output(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        output = _parse_output(d.pop("output"))

        fail_reel = []
        _fail_reel = d.pop("fail_reel")
        for fail_reel_item_data in _fail_reel:
            fail_reel_item = TraceEvidenceFailReelItem.from_dict(fail_reel_item_data)

            fail_reel.append(fail_reel_item)

        pass_reel = []
        _pass_reel = d.pop("pass_reel")
        for pass_reel_item_data in _pass_reel:
            pass_reel_item = TraceEvidencePassReelItem.from_dict(pass_reel_item_data)

            pass_reel.append(pass_reel_item)

        trace_evidence = cls(
            input_=input_,
            output=output,
            fail_reel=fail_reel,
            pass_reel=pass_reel,
        )

        trace_evidence.additional_properties = d
        return trace_evidence

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
