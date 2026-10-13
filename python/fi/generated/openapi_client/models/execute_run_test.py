from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExecuteRunTest")


@_attrs_define
class ExecuteRunTest:
    """
    Attributes:
        scenario_ids (list[UUID] | Unset):
        simulator_id (None | Unset | UUID):
        select_all (bool | Unset):  Default: False.
    """

    scenario_ids: list[UUID] | Unset = UNSET
    simulator_id: None | Unset | UUID = UNSET
    select_all: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scenario_ids: list[str] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = []
            for scenario_ids_item_data in self.scenario_ids:
                scenario_ids_item = str(scenario_ids_item_data)
                scenario_ids.append(scenario_ids_item)

        simulator_id: None | str | Unset
        if isinstance(self.simulator_id, Unset):
            simulator_id = UNSET
        elif isinstance(self.simulator_id, UUID):
            simulator_id = str(self.simulator_id)
        else:
            simulator_id = self.simulator_id

        select_all = self.select_all

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids
        if simulator_id is not UNSET:
            field_dict["simulator_id"] = simulator_id
        if select_all is not UNSET:
            field_dict["select_all"] = select_all

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: list[UUID] | Unset = UNSET
        if _scenario_ids is not UNSET:
            scenario_ids = []
            for scenario_ids_item_data in _scenario_ids:
                scenario_ids_item = UUID(scenario_ids_item_data)

                scenario_ids.append(scenario_ids_item)

        def _parse_simulator_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                simulator_id_type_0 = UUID(data)

                return simulator_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        simulator_id = _parse_simulator_id(d.pop("simulator_id", UNSET))

        select_all = d.pop("select_all", UNSET)

        execute_run_test = cls(
            scenario_ids=scenario_ids,
            simulator_id=simulator_id,
            select_all=select_all,
        )

        execute_run_test.additional_properties = d
        return execute_run_test

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
