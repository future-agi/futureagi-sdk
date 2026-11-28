from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PatternInsightEvidence")


@_attrs_define
class PatternInsightEvidence:
    """
    Attributes:
        test (str | Unset):
        baseline (str | Unset):
        tool (str | Unset):
        z (float | Unset):
        p_value (float | Unset):
        ks_stat (float | Unset):
        fail_median (float | Unset):
        baseline_median (float | Unset):
        fail_pct (int | Unset):
        baseline_pct (int | Unset):
        hits (int | Unset):
        total (int | Unset):
        missing_in (int | Unset):
        traces_with_tools (int | Unset):
    """

    test: str | Unset = UNSET
    baseline: str | Unset = UNSET
    tool: str | Unset = UNSET
    z: float | Unset = UNSET
    p_value: float | Unset = UNSET
    ks_stat: float | Unset = UNSET
    fail_median: float | Unset = UNSET
    baseline_median: float | Unset = UNSET
    fail_pct: int | Unset = UNSET
    baseline_pct: int | Unset = UNSET
    hits: int | Unset = UNSET
    total: int | Unset = UNSET
    missing_in: int | Unset = UNSET
    traces_with_tools: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test = self.test

        baseline = self.baseline

        tool = self.tool

        z = self.z

        p_value = self.p_value

        ks_stat = self.ks_stat

        fail_median = self.fail_median

        baseline_median = self.baseline_median

        fail_pct = self.fail_pct

        baseline_pct = self.baseline_pct

        hits = self.hits

        total = self.total

        missing_in = self.missing_in

        traces_with_tools = self.traces_with_tools

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if test is not UNSET:
            field_dict["test"] = test
        if baseline is not UNSET:
            field_dict["baseline"] = baseline
        if tool is not UNSET:
            field_dict["tool"] = tool
        if z is not UNSET:
            field_dict["z"] = z
        if p_value is not UNSET:
            field_dict["p_value"] = p_value
        if ks_stat is not UNSET:
            field_dict["ks_stat"] = ks_stat
        if fail_median is not UNSET:
            field_dict["fail_median"] = fail_median
        if baseline_median is not UNSET:
            field_dict["baseline_median"] = baseline_median
        if fail_pct is not UNSET:
            field_dict["fail_pct"] = fail_pct
        if baseline_pct is not UNSET:
            field_dict["baseline_pct"] = baseline_pct
        if hits is not UNSET:
            field_dict["hits"] = hits
        if total is not UNSET:
            field_dict["total"] = total
        if missing_in is not UNSET:
            field_dict["missing_in"] = missing_in
        if traces_with_tools is not UNSET:
            field_dict["traces_with_tools"] = traces_with_tools

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        test = d.pop("test", UNSET)

        baseline = d.pop("baseline", UNSET)

        tool = d.pop("tool", UNSET)

        z = d.pop("z", UNSET)

        p_value = d.pop("p_value", UNSET)

        ks_stat = d.pop("ks_stat", UNSET)

        fail_median = d.pop("fail_median", UNSET)

        baseline_median = d.pop("baseline_median", UNSET)

        fail_pct = d.pop("fail_pct", UNSET)

        baseline_pct = d.pop("baseline_pct", UNSET)

        hits = d.pop("hits", UNSET)

        total = d.pop("total", UNSET)

        missing_in = d.pop("missing_in", UNSET)

        traces_with_tools = d.pop("traces_with_tools", UNSET)

        pattern_insight_evidence = cls(
            test=test,
            baseline=baseline,
            tool=tool,
            z=z,
            p_value=p_value,
            ks_stat=ks_stat,
            fail_median=fail_median,
            baseline_median=baseline_median,
            fail_pct=fail_pct,
            baseline_pct=baseline_pct,
            hits=hits,
            total=total,
            missing_in=missing_in,
            traces_with_tools=traces_with_tools,
        )

        pattern_insight_evidence.additional_properties = d
        return pattern_insight_evidence

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
