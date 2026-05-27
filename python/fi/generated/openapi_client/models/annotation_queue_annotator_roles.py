from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.annotation_queue_annotator_roles_additional_property import (
        AnnotationQueueAnnotatorRolesAdditionalProperty,
    )


T = TypeVar("T", bound="AnnotationQueueAnnotatorRoles")


@_attrs_define
class AnnotationQueueAnnotatorRoles:
    """ """

    additional_properties: dict[
        str, AnnotationQueueAnnotatorRolesAdditionalProperty
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_queue_annotator_roles_additional_property import (
            AnnotationQueueAnnotatorRolesAdditionalProperty,
        )

        d = dict(src_dict)
        annotation_queue_annotator_roles = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = (
                AnnotationQueueAnnotatorRolesAdditionalProperty.from_dict(prop_dict)
            )

            additional_properties[prop_name] = additional_property

        annotation_queue_annotator_roles.additional_properties = additional_properties
        return annotation_queue_annotator_roles

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> AnnotationQueueAnnotatorRolesAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(
        self, key: str, value: AnnotationQueueAnnotatorRolesAdditionalProperty
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
