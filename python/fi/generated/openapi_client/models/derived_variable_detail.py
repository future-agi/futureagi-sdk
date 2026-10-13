from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.derived_variable_detail_raw_sample import (
        DerivedVariableDetailRawSample,
    )
    from ..models.derived_variable_detail_schema import DerivedVariableDetailSchema


T = TypeVar("T", bound="DerivedVariableDetail")


@_attrs_define
class DerivedVariableDetail:
    """
    Attributes:
        paths (list[str] | Unset):
        schema (DerivedVariableDetailSchema | Unset):
        full_variables (list[str] | Unset):
        raw_sample (DerivedVariableDetailRawSample | Unset):
        is_json (bool | Unset):
    """

    paths: list[str] | Unset = UNSET
    schema: DerivedVariableDetailSchema | Unset = UNSET
    full_variables: list[str] | Unset = UNSET
    raw_sample: DerivedVariableDetailRawSample | Unset = UNSET
    is_json: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        paths: list[str] | Unset = UNSET
        if not isinstance(self.paths, Unset):
            paths = self.paths

        schema: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schema, Unset):
            schema = self.schema.to_dict()

        full_variables: list[str] | Unset = UNSET
        if not isinstance(self.full_variables, Unset):
            full_variables = self.full_variables

        raw_sample: dict[str, Any] | Unset = UNSET
        if not isinstance(self.raw_sample, Unset):
            raw_sample = self.raw_sample.to_dict()

        is_json = self.is_json

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if paths is not UNSET:
            field_dict["paths"] = paths
        if schema is not UNSET:
            field_dict["schema"] = schema
        if full_variables is not UNSET:
            field_dict["full_variables"] = full_variables
        if raw_sample is not UNSET:
            field_dict["raw_sample"] = raw_sample
        if is_json is not UNSET:
            field_dict["is_json"] = is_json

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.derived_variable_detail_raw_sample import (
            DerivedVariableDetailRawSample,
        )
        from ..models.derived_variable_detail_schema import DerivedVariableDetailSchema

        d = dict(src_dict)
        paths = cast(list[str], d.pop("paths", UNSET))

        _schema = d.pop("schema", UNSET)
        schema: DerivedVariableDetailSchema | Unset
        if isinstance(_schema, Unset):
            schema = UNSET
        else:
            schema = DerivedVariableDetailSchema.from_dict(_schema)

        full_variables = cast(list[str], d.pop("full_variables", UNSET))

        _raw_sample = d.pop("raw_sample", UNSET)
        raw_sample: DerivedVariableDetailRawSample | Unset
        if isinstance(_raw_sample, Unset):
            raw_sample = UNSET
        else:
            raw_sample = DerivedVariableDetailRawSample.from_dict(_raw_sample)

        is_json = d.pop("is_json", UNSET)

        derived_variable_detail = cls(
            paths=paths,
            schema=schema,
            full_variables=full_variables,
            raw_sample=raw_sample,
            is_json=is_json,
        )

        derived_variable_detail.additional_properties = d
        return derived_variable_detail

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
