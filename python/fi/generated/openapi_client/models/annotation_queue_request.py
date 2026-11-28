from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.annotation_queue_request_assignment_strategy import (
    AnnotationQueueRequestAssignmentStrategy,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotation_queue_request_annotator_roles import (
        AnnotationQueueRequestAnnotatorRoles,
    )


T = TypeVar("T", bound="AnnotationQueueRequest")


@_attrs_define
class AnnotationQueueRequest:
    """
    Attributes:
        name (str):
        label_ids (list[UUID]):
        description (None | str | Unset):
        instructions (None | str | Unset):
        assignment_strategy (AnnotationQueueRequestAssignmentStrategy | Unset):
        annotations_required (int | Unset):
        reservation_timeout_minutes (int | Unset):
        requires_review (bool | Unset):
        auto_assign (bool | Unset): When enabled, all queue members can annotate any item without explicit assignment.
        annotator_ids (list[UUID] | Unset):
        annotator_roles (AnnotationQueueRequestAnnotatorRoles | Unset):
    """

    name: str
    label_ids: list[UUID]
    description: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    assignment_strategy: AnnotationQueueRequestAssignmentStrategy | Unset = UNSET
    annotations_required: int | Unset = UNSET
    reservation_timeout_minutes: int | Unset = UNSET
    requires_review: bool | Unset = UNSET
    auto_assign: bool | Unset = UNSET
    annotator_ids: list[UUID] | Unset = UNSET
    annotator_roles: AnnotationQueueRequestAnnotatorRoles | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        label_ids = []
        for label_ids_item_data in self.label_ids:
            label_ids_item = str(label_ids_item_data)
            label_ids.append(label_ids_item)

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        instructions: None | str | Unset
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        else:
            instructions = self.instructions

        assignment_strategy: str | Unset = UNSET
        if not isinstance(self.assignment_strategy, Unset):
            assignment_strategy = self.assignment_strategy.value

        annotations_required = self.annotations_required

        reservation_timeout_minutes = self.reservation_timeout_minutes

        requires_review = self.requires_review

        auto_assign = self.auto_assign

        annotator_ids: list[str] | Unset = UNSET
        if not isinstance(self.annotator_ids, Unset):
            annotator_ids = []
            for annotator_ids_item_data in self.annotator_ids:
                annotator_ids_item = str(annotator_ids_item_data)
                annotator_ids.append(annotator_ids_item)

        annotator_roles: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotator_roles, Unset):
            annotator_roles = self.annotator_roles.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "label_ids": label_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if assignment_strategy is not UNSET:
            field_dict["assignment_strategy"] = assignment_strategy
        if annotations_required is not UNSET:
            field_dict["annotations_required"] = annotations_required
        if reservation_timeout_minutes is not UNSET:
            field_dict["reservation_timeout_minutes"] = reservation_timeout_minutes
        if requires_review is not UNSET:
            field_dict["requires_review"] = requires_review
        if auto_assign is not UNSET:
            field_dict["auto_assign"] = auto_assign
        if annotator_ids is not UNSET:
            field_dict["annotator_ids"] = annotator_ids
        if annotator_roles is not UNSET:
            field_dict["annotator_roles"] = annotator_roles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_queue_request_annotator_roles import (
            AnnotationQueueRequestAnnotatorRoles,
        )

        d = dict(src_dict)
        name = d.pop("name")

        label_ids = []
        _label_ids = d.pop("label_ids")
        for label_ids_item_data in _label_ids:
            label_ids_item = UUID(label_ids_item_data)

            label_ids.append(label_ids_item)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_instructions(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        _assignment_strategy = d.pop("assignment_strategy", UNSET)
        assignment_strategy: AnnotationQueueRequestAssignmentStrategy | Unset
        if isinstance(_assignment_strategy, Unset):
            assignment_strategy = UNSET
        else:
            assignment_strategy = AnnotationQueueRequestAssignmentStrategy(
                _assignment_strategy
            )

        annotations_required = d.pop("annotations_required", UNSET)

        reservation_timeout_minutes = d.pop("reservation_timeout_minutes", UNSET)

        requires_review = d.pop("requires_review", UNSET)

        auto_assign = d.pop("auto_assign", UNSET)

        _annotator_ids = d.pop("annotator_ids", UNSET)
        annotator_ids: list[UUID] | Unset = UNSET
        if _annotator_ids is not UNSET:
            annotator_ids = []
            for annotator_ids_item_data in _annotator_ids:
                annotator_ids_item = UUID(annotator_ids_item_data)

                annotator_ids.append(annotator_ids_item)

        _annotator_roles = d.pop("annotator_roles", UNSET)
        annotator_roles: AnnotationQueueRequestAnnotatorRoles | Unset
        if isinstance(_annotator_roles, Unset):
            annotator_roles = UNSET
        else:
            annotator_roles = AnnotationQueueRequestAnnotatorRoles.from_dict(
                _annotator_roles
            )

        annotation_queue_request = cls(
            name=name,
            label_ids=label_ids,
            description=description,
            instructions=instructions,
            assignment_strategy=assignment_strategy,
            annotations_required=annotations_required,
            reservation_timeout_minutes=reservation_timeout_minutes,
            requires_review=requires_review,
            auto_assign=auto_assign,
            annotator_ids=annotator_ids,
            annotator_roles=annotator_roles,
        )

        annotation_queue_request.additional_properties = d
        return annotation_queue_request

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
