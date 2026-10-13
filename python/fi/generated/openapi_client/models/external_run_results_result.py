from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.external_run_header import ExternalRunHeader
    from ..models.external_run_item_receipt import ExternalRunItemReceipt


T = TypeVar("T", bound="ExternalRunResultsResult")


@_attrs_define
class ExternalRunResultsResult:
    """
    Attributes:
        run (ExternalRunHeader):
        items (list[ExternalRunItemReceipt]):
    """

    run: ExternalRunHeader
    items: list[ExternalRunItemReceipt]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run = self.run.to_dict()

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run": run,
                "items": items,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_header import ExternalRunHeader
        from ..models.external_run_item_receipt import ExternalRunItemReceipt

        d = dict(src_dict)
        run = ExternalRunHeader.from_dict(d.pop("run"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = ExternalRunItemReceipt.from_dict(items_item_data)

            items.append(items_item)

        external_run_results_result = cls(
            run=run,
            items=items,
        )

        external_run_results_result.additional_properties = d
        return external_run_results_result

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
