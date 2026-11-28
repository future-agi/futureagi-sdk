from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SidebarAIMetadata")


@_attrs_define
class SidebarAIMetadata:
    """
    Attributes:
        model (None | str):
        model_version (None | str):
        project (None | str):
        eval_score (float | None):
        trace_id (None | str):
    """

    model: None | str
    model_version: None | str
    project: None | str
    eval_score: float | None
    trace_id: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model: None | str
        model = self.model

        model_version: None | str
        model_version = self.model_version

        project: None | str
        project = self.project

        eval_score: float | None
        eval_score = self.eval_score

        trace_id: None | str
        trace_id = self.trace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model": model,
                "model_version": model_version,
                "project": project,
                "eval_score": eval_score,
                "trace_id": trace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model = _parse_model(d.pop("model"))

        def _parse_model_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model_version = _parse_model_version(d.pop("model_version"))

        def _parse_project(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project = _parse_project(d.pop("project"))

        def _parse_eval_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        eval_score = _parse_eval_score(d.pop("eval_score"))

        def _parse_trace_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trace_id = _parse_trace_id(d.pop("trace_id"))

        sidebar_ai_metadata = cls(
            model=model,
            model_version=model_version,
            project=project,
            eval_score=eval_score,
            trace_id=trace_id,
        )

        sidebar_ai_metadata.additional_properties = d
        return sidebar_ai_metadata

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
