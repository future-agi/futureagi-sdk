from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.output_diff_comparison_missing_side import OutputDiffComparisonMissingSide
from ..models.output_diff_comparison_status import OutputDiffComparisonStatus

T = TypeVar("T", bound="OutputDiffComparison")


@_attrs_define
class OutputDiffComparison:
    """
    Attributes:
        status (OutputDiffComparisonStatus):
        missing_side (None | OutputDiffComparisonMissingSide):
        changed_paths (list[str]):
        changed_path_count (int | None):
        truncated (bool):
    """

    status: OutputDiffComparisonStatus
    missing_side: None | OutputDiffComparisonMissingSide
    changed_paths: list[str]
    changed_path_count: int | None
    truncated: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        missing_side: None | str
        if isinstance(self.missing_side, OutputDiffComparisonMissingSide):
            missing_side = self.missing_side.value
        else:
            missing_side = self.missing_side

        changed_paths = self.changed_paths

        changed_path_count: int | None
        changed_path_count = self.changed_path_count

        truncated = self.truncated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "missing_side": missing_side,
                "changed_paths": changed_paths,
                "changed_path_count": changed_path_count,
                "truncated": truncated,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = OutputDiffComparisonStatus(d.pop("status"))

        def _parse_missing_side(data: object) -> None | OutputDiffComparisonMissingSide:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                missing_side_type_1 = OutputDiffComparisonMissingSide(data)

                return missing_side_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OutputDiffComparisonMissingSide, data)

        missing_side = _parse_missing_side(d.pop("missing_side"))

        changed_paths = cast(list[str], d.pop("changed_paths"))

        def _parse_changed_path_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        changed_path_count = _parse_changed_path_count(d.pop("changed_path_count"))

        truncated = d.pop("truncated")

        output_diff_comparison = cls(
            status=status,
            missing_side=missing_side,
            changed_paths=changed_paths,
            changed_path_count=changed_path_count,
            truncated=truncated,
        )

        output_diff_comparison.additional_properties = d
        return output_diff_comparison

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
