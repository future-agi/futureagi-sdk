from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_chart_point import EvalTemplateChartPoint


T = TypeVar("T", bound="EvalTemplateListItem")


@_attrs_define
class EvalTemplateListItem:
    """
    Attributes:
        id (UUID):
        name (str):
        template_type (str):
        eval_type (str):
        output_type (str):
        owner (str):
        created_by_name (str):
        version_count (int):
        current_version (str):
        last_updated (str):
        thirty_day_chart (list[EvalTemplateChartPoint]):
        thirty_day_error_rate (list[EvalTemplateChartPoint]):
        thirty_day_run_count (int):
        tags (list[str]):
    """

    id: UUID
    name: str
    template_type: str
    eval_type: str
    output_type: str
    owner: str
    created_by_name: str
    version_count: int
    current_version: str
    last_updated: str
    thirty_day_chart: list[EvalTemplateChartPoint]
    thirty_day_error_rate: list[EvalTemplateChartPoint]
    thirty_day_run_count: int
    tags: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        template_type = self.template_type

        eval_type = self.eval_type

        output_type = self.output_type

        owner = self.owner

        created_by_name = self.created_by_name

        version_count = self.version_count

        current_version = self.current_version

        last_updated = self.last_updated

        thirty_day_chart = []
        for thirty_day_chart_item_data in self.thirty_day_chart:
            thirty_day_chart_item = thirty_day_chart_item_data.to_dict()
            thirty_day_chart.append(thirty_day_chart_item)

        thirty_day_error_rate = []
        for thirty_day_error_rate_item_data in self.thirty_day_error_rate:
            thirty_day_error_rate_item = thirty_day_error_rate_item_data.to_dict()
            thirty_day_error_rate.append(thirty_day_error_rate_item)

        thirty_day_run_count = self.thirty_day_run_count

        tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "template_type": template_type,
                "eval_type": eval_type,
                "output_type": output_type,
                "owner": owner,
                "created_by_name": created_by_name,
                "version_count": version_count,
                "current_version": current_version,
                "last_updated": last_updated,
                "thirty_day_chart": thirty_day_chart,
                "thirty_day_error_rate": thirty_day_error_rate,
                "thirty_day_run_count": thirty_day_run_count,
                "tags": tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_chart_point import EvalTemplateChartPoint

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        template_type = d.pop("template_type")

        eval_type = d.pop("eval_type")

        output_type = d.pop("output_type")

        owner = d.pop("owner")

        created_by_name = d.pop("created_by_name")

        version_count = d.pop("version_count")

        current_version = d.pop("current_version")

        last_updated = d.pop("last_updated")

        thirty_day_chart = []
        _thirty_day_chart = d.pop("thirty_day_chart")
        for thirty_day_chart_item_data in _thirty_day_chart:
            thirty_day_chart_item = EvalTemplateChartPoint.from_dict(
                thirty_day_chart_item_data
            )

            thirty_day_chart.append(thirty_day_chart_item)

        thirty_day_error_rate = []
        _thirty_day_error_rate = d.pop("thirty_day_error_rate")
        for thirty_day_error_rate_item_data in _thirty_day_error_rate:
            thirty_day_error_rate_item = EvalTemplateChartPoint.from_dict(
                thirty_day_error_rate_item_data
            )

            thirty_day_error_rate.append(thirty_day_error_rate_item)

        thirty_day_run_count = d.pop("thirty_day_run_count")

        tags = cast(list[str], d.pop("tags"))

        eval_template_list_item = cls(
            id=id,
            name=name,
            template_type=template_type,
            eval_type=eval_type,
            output_type=output_type,
            owner=owner,
            created_by_name=created_by_name,
            version_count=version_count,
            current_version=current_version,
            last_updated=last_updated,
            thirty_day_chart=thirty_day_chart,
            thirty_day_error_rate=thirty_day_error_rate,
            thirty_day_run_count=thirty_day_run_count,
            tags=tags,
        )

        eval_template_list_item.additional_properties = d
        return eval_template_list_item

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
