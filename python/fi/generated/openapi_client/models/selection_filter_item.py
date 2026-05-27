from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.selection_filter_item_filter_config import (
        SelectionFilterItemFilterConfig,
    )


T = TypeVar("T", bound="SelectionFilterItem")


@_attrs_define
class SelectionFilterItem:
    """
    Attributes:
        column_id (str): Column or attribute id to filter on.
        filter_config (SelectionFilterItemFilterConfig):
        display_name (str | Unset): Optional UI label for chips and saved views.
        source (str | Unset): Optional source surface for mixed-source filters, for example traces, datasets, or
            simulation.
        output_type (str | Unset): Optional metric output type metadata used by eval and annotation filters.
    """

    column_id: str
    filter_config: SelectionFilterItemFilterConfig
    display_name: str | Unset = UNSET
    source: str | Unset = UNSET
    output_type: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        column_id = self.column_id

        filter_config = self.filter_config.to_dict()

        display_name = self.display_name

        source = self.source

        output_type = self.output_type

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "column_id": column_id,
                "filter_config": filter_config,
            }
        )
        if display_name is not UNSET:
            field_dict["display_name"] = display_name
        if source is not UNSET:
            field_dict["source"] = source
        if output_type is not UNSET:
            field_dict["output_type"] = output_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.selection_filter_item_filter_config import (
            SelectionFilterItemFilterConfig,
        )

        d = dict(src_dict)
        column_id = d.pop("column_id")

        filter_config = SelectionFilterItemFilterConfig.from_dict(
            d.pop("filter_config")
        )

        display_name = d.pop("display_name", UNSET)

        source = d.pop("source", UNSET)

        output_type = d.pop("output_type", UNSET)

        selection_filter_item = cls(
            column_id=column_id,
            filter_config=filter_config,
            display_name=display_name,
            source=source,
            output_type=output_type,
        )

        return selection_filter_item
