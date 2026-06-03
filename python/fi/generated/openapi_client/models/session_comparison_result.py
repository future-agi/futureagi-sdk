from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_comparison_result_comparison_metrics import (
        SessionComparisonResultComparisonMetrics,
    )
    from ..models.session_comparison_result_comparison_recordings import (
        SessionComparisonResultComparisonRecordings,
    )
    from ..models.session_comparison_result_comparison_transcripts import (
        SessionComparisonResultComparisonTranscripts,
    )


T = TypeVar("T", bound="SessionComparisonResult")


@_attrs_define
class SessionComparisonResult:
    """
    Attributes:
        comparison_metrics (SessionComparisonResultComparisonMetrics | Unset):
        comparison_transcripts (SessionComparisonResultComparisonTranscripts | Unset):
        comparison_recordings (SessionComparisonResultComparisonRecordings | Unset):
    """

    comparison_metrics: SessionComparisonResultComparisonMetrics | Unset = UNSET
    comparison_transcripts: SessionComparisonResultComparisonTranscripts | Unset = UNSET
    comparison_recordings: SessionComparisonResultComparisonRecordings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        comparison_metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.comparison_metrics, Unset):
            comparison_metrics = self.comparison_metrics.to_dict()

        comparison_transcripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.comparison_transcripts, Unset):
            comparison_transcripts = self.comparison_transcripts.to_dict()

        comparison_recordings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.comparison_recordings, Unset):
            comparison_recordings = self.comparison_recordings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if comparison_metrics is not UNSET:
            field_dict["comparison_metrics"] = comparison_metrics
        if comparison_transcripts is not UNSET:
            field_dict["comparison_transcripts"] = comparison_transcripts
        if comparison_recordings is not UNSET:
            field_dict["comparison_recordings"] = comparison_recordings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_comparison_result_comparison_metrics import (
            SessionComparisonResultComparisonMetrics,
        )
        from ..models.session_comparison_result_comparison_recordings import (
            SessionComparisonResultComparisonRecordings,
        )
        from ..models.session_comparison_result_comparison_transcripts import (
            SessionComparisonResultComparisonTranscripts,
        )

        d = dict(src_dict)
        _comparison_metrics = d.pop("comparison_metrics", UNSET)
        comparison_metrics: SessionComparisonResultComparisonMetrics | Unset
        if isinstance(_comparison_metrics, Unset):
            comparison_metrics = UNSET
        else:
            comparison_metrics = SessionComparisonResultComparisonMetrics.from_dict(
                _comparison_metrics
            )

        _comparison_transcripts = d.pop("comparison_transcripts", UNSET)
        comparison_transcripts: SessionComparisonResultComparisonTranscripts | Unset
        if isinstance(_comparison_transcripts, Unset):
            comparison_transcripts = UNSET
        else:
            comparison_transcripts = (
                SessionComparisonResultComparisonTranscripts.from_dict(
                    _comparison_transcripts
                )
            )

        _comparison_recordings = d.pop("comparison_recordings", UNSET)
        comparison_recordings: SessionComparisonResultComparisonRecordings | Unset
        if isinstance(_comparison_recordings, Unset):
            comparison_recordings = UNSET
        else:
            comparison_recordings = (
                SessionComparisonResultComparisonRecordings.from_dict(
                    _comparison_recordings
                )
            )

        session_comparison_result = cls(
            comparison_metrics=comparison_metrics,
            comparison_transcripts=comparison_transcripts,
            comparison_recordings=comparison_recordings,
        )

        session_comparison_result.additional_properties = d
        return session_comparison_result

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
