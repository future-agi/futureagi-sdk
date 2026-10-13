from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..models.external_run_item_receipt_status import ExternalRunItemReceiptStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.external_run_score import ExternalRunScore


T = TypeVar("T", bound="ExternalRunItemReceipt")


@_attrs_define
class ExternalRunItemReceipt:
    """
    Attributes:
        example_id (UUID):
        id (UUID):
        receipt_key (str):
        status (ExternalRunItemReceiptStatus):
        trace_id (None | str):
        root_span_id (None | str):
        score_refs (list[ExternalRunScore]):
        trial_number (int | Unset):  Default: 1.
    """

    example_id: UUID
    id: UUID
    receipt_key: str
    status: ExternalRunItemReceiptStatus
    trace_id: None | str
    root_span_id: None | str
    score_refs: list[ExternalRunScore]
    trial_number: int | Unset = 1

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        id = str(self.id)

        receipt_key = self.receipt_key

        status = self.status.value

        trace_id: None | str
        trace_id = self.trace_id

        root_span_id: None | str
        root_span_id = self.root_span_id

        score_refs = []
        for score_refs_item_data in self.score_refs:
            score_refs_item = score_refs_item_data.to_dict()
            score_refs.append(score_refs_item)

        trial_number = self.trial_number

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "example_id": example_id,
                "id": id,
                "receipt_key": receipt_key,
                "status": status,
                "trace_id": trace_id,
                "root_span_id": root_span_id,
                "score_refs": score_refs,
            }
        )
        if trial_number is not UNSET:
            field_dict["trial_number"] = trial_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_run_score import ExternalRunScore

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        id = UUID(d.pop("id"))

        receipt_key = d.pop("receipt_key")

        status = ExternalRunItemReceiptStatus(d.pop("status"))

        def _parse_trace_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trace_id = _parse_trace_id(d.pop("trace_id"))

        def _parse_root_span_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        root_span_id = _parse_root_span_id(d.pop("root_span_id"))

        score_refs = []
        _score_refs = d.pop("score_refs")
        for score_refs_item_data in _score_refs:
            score_refs_item = ExternalRunScore.from_dict(score_refs_item_data)

            score_refs.append(score_refs_item)

        trial_number = d.pop("trial_number", UNSET)

        external_run_item_receipt = cls(
            example_id=example_id,
            id=id,
            receipt_key=receipt_key,
            status=status,
            trace_id=trace_id,
            root_span_id=root_span_id,
            score_refs=score_refs,
            trial_number=trial_number,
        )

        return external_run_item_receipt
