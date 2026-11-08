from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bulk_annotation_response_result_errors_type_0_item import (
        BulkAnnotationResponseResultErrorsType0Item,
    )
    from ..models.bulk_annotation_response_result_warnings_type_0_item import (
        BulkAnnotationResponseResultWarningsType0Item,
    )


T = TypeVar("T", bound="BulkAnnotationResponseResult")


@_attrs_define
class BulkAnnotationResponseResult:
    """
    Attributes:
        message (str):
        annotations_created (int):
        annotations_updated (int):
        notes_created (int):
        succeeded_count (int):
        errors_count (int):
        warnings_count (int):
        warnings (list[BulkAnnotationResponseResultWarningsType0Item] | None | Unset):
        errors (list[BulkAnnotationResponseResultErrorsType0Item] | None | Unset):
    """

    message: str
    annotations_created: int
    annotations_updated: int
    notes_created: int
    succeeded_count: int
    errors_count: int
    warnings_count: int
    warnings: list[BulkAnnotationResponseResultWarningsType0Item] | None | Unset = UNSET
    errors: list[BulkAnnotationResponseResultErrorsType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        annotations_created = self.annotations_created

        annotations_updated = self.annotations_updated

        notes_created = self.notes_created

        succeeded_count = self.succeeded_count

        errors_count = self.errors_count

        warnings_count = self.warnings_count

        warnings: list[dict[str, Any]] | None | Unset
        if isinstance(self.warnings, Unset):
            warnings = UNSET
        elif isinstance(self.warnings, list):
            warnings = []
            for warnings_type_0_item_data in self.warnings:
                warnings_type_0_item = warnings_type_0_item_data.to_dict()
                warnings.append(warnings_type_0_item)

        else:
            warnings = self.warnings

        errors: list[dict[str, Any]] | None | Unset
        if isinstance(self.errors, Unset):
            errors = UNSET
        elif isinstance(self.errors, list):
            errors = []
            for errors_type_0_item_data in self.errors:
                errors_type_0_item = errors_type_0_item_data.to_dict()
                errors.append(errors_type_0_item)

        else:
            errors = self.errors

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "annotations_created": annotations_created,
                "annotations_updated": annotations_updated,
                "notes_created": notes_created,
                "succeeded_count": succeeded_count,
                "errors_count": errors_count,
                "warnings_count": warnings_count,
            }
        )
        if warnings is not UNSET:
            field_dict["warnings"] = warnings
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bulk_annotation_response_result_errors_type_0_item import (
            BulkAnnotationResponseResultErrorsType0Item,
        )
        from ..models.bulk_annotation_response_result_warnings_type_0_item import (
            BulkAnnotationResponseResultWarningsType0Item,
        )

        d = dict(src_dict)
        message = d.pop("message")

        annotations_created = d.pop("annotations_created")

        annotations_updated = d.pop("annotations_updated")

        notes_created = d.pop("notes_created")

        succeeded_count = d.pop("succeeded_count")

        errors_count = d.pop("errors_count")

        warnings_count = d.pop("warnings_count")

        def _parse_warnings(
            data: object,
        ) -> list[BulkAnnotationResponseResultWarningsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                warnings_type_0 = []
                _warnings_type_0 = data
                for warnings_type_0_item_data in _warnings_type_0:
                    warnings_type_0_item = (
                        BulkAnnotationResponseResultWarningsType0Item.from_dict(
                            warnings_type_0_item_data
                        )
                    )

                    warnings_type_0.append(warnings_type_0_item)

                return warnings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[BulkAnnotationResponseResultWarningsType0Item] | None | Unset, data
            )

        warnings = _parse_warnings(d.pop("warnings", UNSET))

        def _parse_errors(
            data: object,
        ) -> list[BulkAnnotationResponseResultErrorsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                errors_type_0 = []
                _errors_type_0 = data
                for errors_type_0_item_data in _errors_type_0:
                    errors_type_0_item = (
                        BulkAnnotationResponseResultErrorsType0Item.from_dict(
                            errors_type_0_item_data
                        )
                    )

                    errors_type_0.append(errors_type_0_item)

                return errors_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[BulkAnnotationResponseResultErrorsType0Item] | None | Unset, data
            )

        errors = _parse_errors(d.pop("errors", UNSET))

        bulk_annotation_response_result = cls(
            message=message,
            annotations_created=annotations_created,
            annotations_updated=annotations_updated,
            notes_created=notes_created,
            succeeded_count=succeeded_count,
            errors_count=errors_count,
            warnings_count=warnings_count,
            warnings=warnings,
            errors=errors,
        )

        bulk_annotation_response_result.additional_properties = d
        return bulk_annotation_response_result

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
