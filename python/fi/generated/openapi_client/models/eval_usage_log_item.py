from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_feedback import EvalUsageFeedback
    from ..models.eval_usage_log_item_detail import EvalUsageLogItemDetail


T = TypeVar("T", bound="EvalUsageLogItem")


@_attrs_define
class EvalUsageLogItem:
    """
    Attributes:
        id (UUID):
        input_ (str):
        status (str):
        created_at (str):
        detail (EvalUsageLogItemDetail):
        result (str | Unset):
        score (float | None | Unset):
        reason (str | Unset):
        source (str | Unset):
        feedback (EvalUsageFeedback | Unset):
        composite (bool | Unset):
        aggregate_pass (bool | None | Unset):
    """

    id: UUID
    input_: str
    status: str
    created_at: str
    detail: EvalUsageLogItemDetail
    result: str | Unset = UNSET
    score: float | None | Unset = UNSET
    reason: str | Unset = UNSET
    source: str | Unset = UNSET
    feedback: EvalUsageFeedback | Unset = UNSET
    composite: bool | Unset = UNSET
    aggregate_pass: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        input_ = self.input_

        status = self.status

        created_at = self.created_at

        detail = self.detail.to_dict()

        result = self.result

        score: float | None | Unset
        if isinstance(self.score, Unset):
            score = UNSET
        else:
            score = self.score

        reason = self.reason

        source = self.source

        feedback: dict[str, Any] | Unset = UNSET
        if not isinstance(self.feedback, Unset):
            feedback = self.feedback.to_dict()

        composite = self.composite

        aggregate_pass: bool | None | Unset
        if isinstance(self.aggregate_pass, Unset):
            aggregate_pass = UNSET
        else:
            aggregate_pass = self.aggregate_pass

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "input": input_,
                "status": status,
                "created_at": created_at,
                "detail": detail,
            }
        )
        if result is not UNSET:
            field_dict["result"] = result
        if score is not UNSET:
            field_dict["score"] = score
        if reason is not UNSET:
            field_dict["reason"] = reason
        if source is not UNSET:
            field_dict["source"] = source
        if feedback is not UNSET:
            field_dict["feedback"] = feedback
        if composite is not UNSET:
            field_dict["composite"] = composite
        if aggregate_pass is not UNSET:
            field_dict["aggregate_pass"] = aggregate_pass

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_feedback import EvalUsageFeedback
        from ..models.eval_usage_log_item_detail import EvalUsageLogItemDetail

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        input_ = d.pop("input")

        status = d.pop("status")

        created_at = d.pop("created_at")

        detail = EvalUsageLogItemDetail.from_dict(d.pop("detail"))

        result = d.pop("result", UNSET)

        def _parse_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        score = _parse_score(d.pop("score", UNSET))

        reason = d.pop("reason", UNSET)

        source = d.pop("source", UNSET)

        _feedback = d.pop("feedback", UNSET)
        feedback: EvalUsageFeedback | Unset
        if isinstance(_feedback, Unset):
            feedback = UNSET
        else:
            feedback = EvalUsageFeedback.from_dict(_feedback)

        composite = d.pop("composite", UNSET)

        def _parse_aggregate_pass(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        aggregate_pass = _parse_aggregate_pass(d.pop("aggregate_pass", UNSET))

        eval_usage_log_item = cls(
            id=id,
            input_=input_,
            status=status,
            created_at=created_at,
            detail=detail,
            result=result,
            score=score,
            reason=reason,
            source=source,
            feedback=feedback,
            composite=composite,
            aggregate_pass=aggregate_pass,
        )

        eval_usage_log_item.additional_properties = d
        return eval_usage_log_item

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
