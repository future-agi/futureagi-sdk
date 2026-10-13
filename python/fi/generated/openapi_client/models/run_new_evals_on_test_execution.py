from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunNewEvalsOnTestExecution")


@_attrs_define
class RunNewEvalsOnTestExecution:
    """
    Attributes:
        eval_config_ids (list[UUID]): List of SimulateEvalConfig IDs to run on the test executions
        test_execution_ids (list[UUID] | Unset): List of specific test execution IDs to run evaluations on
        select_all (bool | Unset): Whether to run evaluations on all test executions in the run test Default: False.
        enable_tool_evaluation (bool | Unset): Whether to enable tool evaluation for this run (if not provided, uses the
            run test's current setting)
    """

    eval_config_ids: list[UUID]
    test_execution_ids: list[UUID] | Unset = UNSET
    select_all: bool | Unset = False
    enable_tool_evaluation: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_config_ids = []
        for eval_config_ids_item_data in self.eval_config_ids:
            eval_config_ids_item = str(eval_config_ids_item_data)
            eval_config_ids.append(eval_config_ids_item)

        test_execution_ids: list[str] | Unset = UNSET
        if not isinstance(self.test_execution_ids, Unset):
            test_execution_ids = []
            for test_execution_ids_item_data in self.test_execution_ids:
                test_execution_ids_item = str(test_execution_ids_item_data)
                test_execution_ids.append(test_execution_ids_item)

        select_all = self.select_all

        enable_tool_evaluation = self.enable_tool_evaluation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_config_ids": eval_config_ids,
            }
        )
        if test_execution_ids is not UNSET:
            field_dict["test_execution_ids"] = test_execution_ids
        if select_all is not UNSET:
            field_dict["select_all"] = select_all
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        eval_config_ids = []
        _eval_config_ids = d.pop("eval_config_ids")
        for eval_config_ids_item_data in _eval_config_ids:
            eval_config_ids_item = UUID(eval_config_ids_item_data)

            eval_config_ids.append(eval_config_ids_item)

        _test_execution_ids = d.pop("test_execution_ids", UNSET)
        test_execution_ids: list[UUID] | Unset = UNSET
        if _test_execution_ids is not UNSET:
            test_execution_ids = []
            for test_execution_ids_item_data in _test_execution_ids:
                test_execution_ids_item = UUID(test_execution_ids_item_data)

                test_execution_ids.append(test_execution_ids_item)

        select_all = d.pop("select_all", UNSET)

        enable_tool_evaluation = d.pop("enable_tool_evaluation", UNSET)

        run_new_evals_on_test_execution = cls(
            eval_config_ids=eval_config_ids,
            test_execution_ids=test_execution_ids,
            select_all=select_all,
            enable_tool_evaluation=enable_tool_evaluation,
        )

        run_new_evals_on_test_execution.additional_properties = d
        return run_new_evals_on_test_execution

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
