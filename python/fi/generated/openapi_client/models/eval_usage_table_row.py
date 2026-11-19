from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_feedback_cell import EvalUsageFeedbackCell
    from ..models.eval_usage_log_item_detail import EvalUsageLogItemDetail
    from ..models.eval_usage_number_cell import EvalUsageNumberCell
    from ..models.eval_usage_string_cell import EvalUsageStringCell
    from ..models.eval_usage_warnings_cell import EvalUsageWarningsCell


T = TypeVar("T", bound="EvalUsageTableRow")


@_attrs_define
class EvalUsageTableRow:
    """
    Attributes:
        row_id (str):
        score (EvalUsageNumberCell | Unset):
        result (EvalUsageStringCell | Unset):
        input_ (EvalUsageStringCell | Unset):
        reason (EvalUsageStringCell | Unset):
        source (EvalUsageStringCell | Unset):
        version (EvalUsageStringCell | Unset):
        feedback (EvalUsageFeedbackCell | Unset):
        created_at (EvalUsageStringCell | Unset):
        status (EvalUsageStringCell | Unset):
        warnings (EvalUsageWarningsCell | Unset):
        detail (EvalUsageLogItemDetail | Unset):
        composite (bool | Unset):
        aggregate_pass (bool | None | Unset):
    """

    row_id: str
    score: EvalUsageNumberCell | Unset = UNSET
    result: EvalUsageStringCell | Unset = UNSET
    input_: EvalUsageStringCell | Unset = UNSET
    reason: EvalUsageStringCell | Unset = UNSET
    source: EvalUsageStringCell | Unset = UNSET
    version: EvalUsageStringCell | Unset = UNSET
    feedback: EvalUsageFeedbackCell | Unset = UNSET
    created_at: EvalUsageStringCell | Unset = UNSET
    status: EvalUsageStringCell | Unset = UNSET
    warnings: EvalUsageWarningsCell | Unset = UNSET
    detail: EvalUsageLogItemDetail | Unset = UNSET
    composite: bool | Unset = UNSET
    aggregate_pass: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_id = self.row_id

        score: dict[str, Any] | Unset = UNSET
        if not isinstance(self.score, Unset):
            score = self.score.to_dict()

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        input_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        reason: dict[str, Any] | Unset = UNSET
        if not isinstance(self.reason, Unset):
            reason = self.reason.to_dict()

        source: dict[str, Any] | Unset = UNSET
        if not isinstance(self.source, Unset):
            source = self.source.to_dict()

        version: dict[str, Any] | Unset = UNSET
        if not isinstance(self.version, Unset):
            version = self.version.to_dict()

        feedback: dict[str, Any] | Unset = UNSET
        if not isinstance(self.feedback, Unset):
            feedback = self.feedback.to_dict()

        created_at: dict[str, Any] | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.to_dict()

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        warnings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings.to_dict()

        detail: dict[str, Any] | Unset = UNSET
        if not isinstance(self.detail, Unset):
            detail = self.detail.to_dict()

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
                "row_id": row_id,
            }
        )
        if score is not UNSET:
            field_dict["score"] = score
        if result is not UNSET:
            field_dict["result"] = result
        if input_ is not UNSET:
            field_dict["input"] = input_
        if reason is not UNSET:
            field_dict["reason"] = reason
        if source is not UNSET:
            field_dict["source"] = source
        if version is not UNSET:
            field_dict["version"] = version
        if feedback is not UNSET:
            field_dict["feedback"] = feedback
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if status is not UNSET:
            field_dict["status"] = status
        if warnings is not UNSET:
            field_dict["warnings"] = warnings
        if detail is not UNSET:
            field_dict["detail"] = detail
        if composite is not UNSET:
            field_dict["composite"] = composite
        if aggregate_pass is not UNSET:
            field_dict["aggregate_pass"] = aggregate_pass

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_feedback_cell import EvalUsageFeedbackCell
        from ..models.eval_usage_log_item_detail import EvalUsageLogItemDetail
        from ..models.eval_usage_number_cell import EvalUsageNumberCell
        from ..models.eval_usage_string_cell import EvalUsageStringCell
        from ..models.eval_usage_warnings_cell import EvalUsageWarningsCell

        d = dict(src_dict)
        row_id = d.pop("row_id")

        _score = d.pop("score", UNSET)
        score: EvalUsageNumberCell | Unset
        if isinstance(_score, Unset):
            score = UNSET
        else:
            score = EvalUsageNumberCell.from_dict(_score)

        _result = d.pop("result", UNSET)
        result: EvalUsageStringCell | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = EvalUsageStringCell.from_dict(_result)

        _input_ = d.pop("input", UNSET)
        input_: EvalUsageStringCell | Unset
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = EvalUsageStringCell.from_dict(_input_)

        _reason = d.pop("reason", UNSET)
        reason: EvalUsageStringCell | Unset
        if isinstance(_reason, Unset):
            reason = UNSET
        else:
            reason = EvalUsageStringCell.from_dict(_reason)

        _source = d.pop("source", UNSET)
        source: EvalUsageStringCell | Unset
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = EvalUsageStringCell.from_dict(_source)

        _version = d.pop("version", UNSET)
        version: EvalUsageStringCell | Unset
        if isinstance(_version, Unset):
            version = UNSET
        else:
            version = EvalUsageStringCell.from_dict(_version)

        _feedback = d.pop("feedback", UNSET)
        feedback: EvalUsageFeedbackCell | Unset
        if isinstance(_feedback, Unset):
            feedback = UNSET
        else:
            feedback = EvalUsageFeedbackCell.from_dict(_feedback)

        _created_at = d.pop("created_at", UNSET)
        created_at: EvalUsageStringCell | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = EvalUsageStringCell.from_dict(_created_at)

        _status = d.pop("status", UNSET)
        status: EvalUsageStringCell | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = EvalUsageStringCell.from_dict(_status)

        _warnings = d.pop("warnings", UNSET)
        warnings: EvalUsageWarningsCell | Unset
        if isinstance(_warnings, Unset):
            warnings = UNSET
        else:
            warnings = EvalUsageWarningsCell.from_dict(_warnings)

        _detail = d.pop("detail", UNSET)
        detail: EvalUsageLogItemDetail | Unset
        if isinstance(_detail, Unset):
            detail = UNSET
        else:
            detail = EvalUsageLogItemDetail.from_dict(_detail)

        composite = d.pop("composite", UNSET)

        def _parse_aggregate_pass(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        aggregate_pass = _parse_aggregate_pass(d.pop("aggregate_pass", UNSET))

        eval_usage_table_row = cls(
            row_id=row_id,
            score=score,
            result=result,
            input_=input_,
            reason=reason,
            source=source,
            version=version,
            feedback=feedback,
            created_at=created_at,
            status=status,
            warnings=warnings,
            detail=detail,
            composite=composite,
            aggregate_pass=aggregate_pass,
        )

        eval_usage_table_row.additional_properties = d
        return eval_usage_table_row

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
