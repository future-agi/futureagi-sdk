from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.annotation_queue_assignment_strategy import (
    AnnotationQueueAssignmentStrategy,
)
from ..models.annotation_queue_status import AnnotationQueueStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotation_queue_annotator_roles import AnnotationQueueAnnotatorRoles
    from ..models.queue_annotator_nested import QueueAnnotatorNested
    from ..models.queue_label_nested import QueueLabelNested


T = TypeVar("T", bound="AnnotationQueue")


@_attrs_define
class AnnotationQueue:
    """
    Attributes:
        name (str):
        id (UUID | Unset):
        description (None | str | Unset):
        instructions (None | str | Unset):
        status (AnnotationQueueStatus | Unset):
        assignment_strategy (AnnotationQueueAssignmentStrategy | Unset):
        annotations_required (int | Unset):
        reservation_timeout_minutes (int | Unset):
        requires_review (bool | Unset):
        auto_assign (bool | Unset): When enabled, all queue members can annotate any item without explicit assignment.
        organization (UUID | Unset):
        project (None | Unset | UUID):
        dataset (None | Unset | UUID):
        agent_definition (None | Unset | UUID):
        is_default (bool | Unset):
        labels (list[QueueLabelNested] | Unset):
        annotators (list[QueueAnnotatorNested] | Unset):
        label_ids (list[UUID] | Unset):
        annotator_ids (list[UUID] | Unset):
        annotator_roles (AnnotationQueueAnnotatorRoles | Unset):
        label_count (int | Unset):
        annotator_count (int | Unset):
        item_count (int | Unset):
        completed_count (int | Unset):
        created_by (None | Unset | UUID):
        created_by_name (str | Unset):
        viewer_role (str | Unset):
        viewer_roles (str | Unset):
        created_at (datetime.datetime | Unset):
    """

    name: str
    id: UUID | Unset = UNSET
    description: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    status: AnnotationQueueStatus | Unset = UNSET
    assignment_strategy: AnnotationQueueAssignmentStrategy | Unset = UNSET
    annotations_required: int | Unset = UNSET
    reservation_timeout_minutes: int | Unset = UNSET
    requires_review: bool | Unset = UNSET
    auto_assign: bool | Unset = UNSET
    organization: UUID | Unset = UNSET
    project: None | Unset | UUID = UNSET
    dataset: None | Unset | UUID = UNSET
    agent_definition: None | Unset | UUID = UNSET
    is_default: bool | Unset = UNSET
    labels: list[QueueLabelNested] | Unset = UNSET
    annotators: list[QueueAnnotatorNested] | Unset = UNSET
    label_ids: list[UUID] | Unset = UNSET
    annotator_ids: list[UUID] | Unset = UNSET
    annotator_roles: AnnotationQueueAnnotatorRoles | Unset = UNSET
    label_count: int | Unset = UNSET
    annotator_count: int | Unset = UNSET
    item_count: int | Unset = UNSET
    completed_count: int | Unset = UNSET
    created_by: None | Unset | UUID = UNSET
    created_by_name: str | Unset = UNSET
    viewer_role: str | Unset = UNSET
    viewer_roles: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

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

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        assignment_strategy: str | Unset = UNSET
        if not isinstance(self.assignment_strategy, Unset):
            assignment_strategy = self.assignment_strategy.value

        annotations_required = self.annotations_required

        reservation_timeout_minutes = self.reservation_timeout_minutes

        requires_review = self.requires_review

        auto_assign = self.auto_assign

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        project: None | str | Unset
        if isinstance(self.project, Unset):
            project = UNSET
        elif isinstance(self.project, UUID):
            project = str(self.project)
        else:
            project = self.project

        dataset: None | str | Unset
        if isinstance(self.dataset, Unset):
            dataset = UNSET
        elif isinstance(self.dataset, UUID):
            dataset = str(self.dataset)
        else:
            dataset = self.dataset

        agent_definition: None | str | Unset
        if isinstance(self.agent_definition, Unset):
            agent_definition = UNSET
        elif isinstance(self.agent_definition, UUID):
            agent_definition = str(self.agent_definition)
        else:
            agent_definition = self.agent_definition

        is_default = self.is_default

        labels: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for labels_item_data in self.labels:
                labels_item = labels_item_data.to_dict()
                labels.append(labels_item)

        annotators: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.annotators, Unset):
            annotators = []
            for annotators_item_data in self.annotators:
                annotators_item = annotators_item_data.to_dict()
                annotators.append(annotators_item)

        label_ids: list[str] | Unset = UNSET
        if not isinstance(self.label_ids, Unset):
            label_ids = []
            for label_ids_item_data in self.label_ids:
                label_ids_item = str(label_ids_item_data)
                label_ids.append(label_ids_item)

        annotator_ids: list[str] | Unset = UNSET
        if not isinstance(self.annotator_ids, Unset):
            annotator_ids = []
            for annotator_ids_item_data in self.annotator_ids:
                annotator_ids_item = str(annotator_ids_item_data)
                annotator_ids.append(annotator_ids_item)

        annotator_roles: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotator_roles, Unset):
            annotator_roles = self.annotator_roles.to_dict()

        label_count = self.label_count

        annotator_count = self.annotator_count

        item_count = self.item_count

        completed_count = self.completed_count

        created_by: None | str | Unset
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        elif isinstance(self.created_by, UUID):
            created_by = str(self.created_by)
        else:
            created_by = self.created_by

        created_by_name = self.created_by_name

        viewer_role = self.viewer_role

        viewer_roles = self.viewer_roles

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if status is not UNSET:
            field_dict["status"] = status
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
        if organization is not UNSET:
            field_dict["organization"] = organization
        if project is not UNSET:
            field_dict["project"] = project
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if agent_definition is not UNSET:
            field_dict["agent_definition"] = agent_definition
        if is_default is not UNSET:
            field_dict["is_default"] = is_default
        if labels is not UNSET:
            field_dict["labels"] = labels
        if annotators is not UNSET:
            field_dict["annotators"] = annotators
        if label_ids is not UNSET:
            field_dict["label_ids"] = label_ids
        if annotator_ids is not UNSET:
            field_dict["annotator_ids"] = annotator_ids
        if annotator_roles is not UNSET:
            field_dict["annotator_roles"] = annotator_roles
        if label_count is not UNSET:
            field_dict["label_count"] = label_count
        if annotator_count is not UNSET:
            field_dict["annotator_count"] = annotator_count
        if item_count is not UNSET:
            field_dict["item_count"] = item_count
        if completed_count is not UNSET:
            field_dict["completed_count"] = completed_count
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_by_name is not UNSET:
            field_dict["created_by_name"] = created_by_name
        if viewer_role is not UNSET:
            field_dict["viewer_role"] = viewer_role
        if viewer_roles is not UNSET:
            field_dict["viewer_roles"] = viewer_roles
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_queue_annotator_roles import (
            AnnotationQueueAnnotatorRoles,
        )
        from ..models.queue_annotator_nested import QueueAnnotatorNested
        from ..models.queue_label_nested import QueueLabelNested

        d = dict(src_dict)
        name = d.pop("name")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

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

        _status = d.pop("status", UNSET)
        status: AnnotationQueueStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = AnnotationQueueStatus(_status)

        _assignment_strategy = d.pop("assignment_strategy", UNSET)
        assignment_strategy: AnnotationQueueAssignmentStrategy | Unset
        if isinstance(_assignment_strategy, Unset):
            assignment_strategy = UNSET
        else:
            assignment_strategy = AnnotationQueueAssignmentStrategy(
                _assignment_strategy
            )

        annotations_required = d.pop("annotations_required", UNSET)

        reservation_timeout_minutes = d.pop("reservation_timeout_minutes", UNSET)

        requires_review = d.pop("requires_review", UNSET)

        auto_assign = d.pop("auto_assign", UNSET)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        def _parse_project(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                project_type_0 = UUID(data)

                return project_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        project = _parse_project(d.pop("project", UNSET))

        def _parse_dataset(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                dataset_type_0 = UUID(data)

                return dataset_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        dataset = _parse_dataset(d.pop("dataset", UNSET))

        def _parse_agent_definition(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_definition_type_0 = UUID(data)

                return agent_definition_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_definition = _parse_agent_definition(d.pop("agent_definition", UNSET))

        is_default = d.pop("is_default", UNSET)

        _labels = d.pop("labels", UNSET)
        labels: list[QueueLabelNested] | Unset = UNSET
        if _labels is not UNSET:
            labels = []
            for labels_item_data in _labels:
                labels_item = QueueLabelNested.from_dict(labels_item_data)

                labels.append(labels_item)

        _annotators = d.pop("annotators", UNSET)
        annotators: list[QueueAnnotatorNested] | Unset = UNSET
        if _annotators is not UNSET:
            annotators = []
            for annotators_item_data in _annotators:
                annotators_item = QueueAnnotatorNested.from_dict(annotators_item_data)

                annotators.append(annotators_item)

        _label_ids = d.pop("label_ids", UNSET)
        label_ids: list[UUID] | Unset = UNSET
        if _label_ids is not UNSET:
            label_ids = []
            for label_ids_item_data in _label_ids:
                label_ids_item = UUID(label_ids_item_data)

                label_ids.append(label_ids_item)

        _annotator_ids = d.pop("annotator_ids", UNSET)
        annotator_ids: list[UUID] | Unset = UNSET
        if _annotator_ids is not UNSET:
            annotator_ids = []
            for annotator_ids_item_data in _annotator_ids:
                annotator_ids_item = UUID(annotator_ids_item_data)

                annotator_ids.append(annotator_ids_item)

        _annotator_roles = d.pop("annotator_roles", UNSET)
        annotator_roles: AnnotationQueueAnnotatorRoles | Unset
        if isinstance(_annotator_roles, Unset):
            annotator_roles = UNSET
        else:
            annotator_roles = AnnotationQueueAnnotatorRoles.from_dict(_annotator_roles)

        label_count = d.pop("label_count", UNSET)

        annotator_count = d.pop("annotator_count", UNSET)

        item_count = d.pop("item_count", UNSET)

        completed_count = d.pop("completed_count", UNSET)

        def _parse_created_by(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_by_type_0 = UUID(data)

                return created_by_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        created_by_name = d.pop("created_by_name", UNSET)

        viewer_role = d.pop("viewer_role", UNSET)

        viewer_roles = d.pop("viewer_roles", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        annotation_queue = cls(
            name=name,
            id=id,
            description=description,
            instructions=instructions,
            status=status,
            assignment_strategy=assignment_strategy,
            annotations_required=annotations_required,
            reservation_timeout_minutes=reservation_timeout_minutes,
            requires_review=requires_review,
            auto_assign=auto_assign,
            organization=organization,
            project=project,
            dataset=dataset,
            agent_definition=agent_definition,
            is_default=is_default,
            labels=labels,
            annotators=annotators,
            label_ids=label_ids,
            annotator_ids=annotator_ids,
            annotator_roles=annotator_roles,
            label_count=label_count,
            annotator_count=annotator_count,
            item_count=item_count,
            completed_count=completed_count,
            created_by=created_by,
            created_by_name=created_by_name,
            viewer_role=viewer_role,
            viewer_roles=viewer_roles,
            created_at=created_at,
        )

        annotation_queue.additional_properties = d
        return annotation_queue

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
