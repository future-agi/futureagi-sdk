from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_for_source_entry_existing_scores_additional_property import (
        QueueForSourceEntryExistingScoresAdditionalProperty,
    )


T = TypeVar("T", bound="QueueForSourceEntryExistingScores")


@_attrs_define
class QueueForSourceEntryExistingScores:
    """ """

    additional_properties: dict[
        str, QueueForSourceEntryExistingScoresAdditionalProperty
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_for_source_entry_existing_scores_additional_property import (
            QueueForSourceEntryExistingScoresAdditionalProperty,
        )

        d = dict(src_dict)
        queue_for_source_entry_existing_scores = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = (
                QueueForSourceEntryExistingScoresAdditionalProperty.from_dict(prop_dict)
            )

            additional_properties[prop_name] = additional_property

        queue_for_source_entry_existing_scores.additional_properties = (
            additional_properties
        )
        return queue_for_source_entry_existing_scores

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> QueueForSourceEntryExistingScoresAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(
        self, key: str, value: QueueForSourceEntryExistingScoresAdditionalProperty
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
