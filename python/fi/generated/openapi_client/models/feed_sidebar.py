from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.co_occurring_issue import CoOccurringIssue
    from ..models.evaluation_result import EvaluationResult
    from ..models.sidebar_ai_metadata import SidebarAIMetadata
    from ..models.sidebar_timeline import SidebarTimeline


T = TypeVar("T", bound="FeedSidebar")


@_attrs_define
class FeedSidebar:
    """
    Attributes:
        timeline (SidebarTimeline):
        ai_metadata (SidebarAIMetadata):
        evaluations (list[EvaluationResult]):
        co_occurring_issues (list[CoOccurringIssue]):
    """

    timeline: SidebarTimeline
    ai_metadata: SidebarAIMetadata
    evaluations: list[EvaluationResult]
    co_occurring_issues: list[CoOccurringIssue]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timeline = self.timeline.to_dict()

        ai_metadata = self.ai_metadata.to_dict()

        evaluations = []
        for evaluations_item_data in self.evaluations:
            evaluations_item = evaluations_item_data.to_dict()
            evaluations.append(evaluations_item)

        co_occurring_issues = []
        for co_occurring_issues_item_data in self.co_occurring_issues:
            co_occurring_issues_item = co_occurring_issues_item_data.to_dict()
            co_occurring_issues.append(co_occurring_issues_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timeline": timeline,
                "ai_metadata": ai_metadata,
                "evaluations": evaluations,
                "co_occurring_issues": co_occurring_issues,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.co_occurring_issue import CoOccurringIssue
        from ..models.evaluation_result import EvaluationResult
        from ..models.sidebar_ai_metadata import SidebarAIMetadata
        from ..models.sidebar_timeline import SidebarTimeline

        d = dict(src_dict)
        timeline = SidebarTimeline.from_dict(d.pop("timeline"))

        ai_metadata = SidebarAIMetadata.from_dict(d.pop("ai_metadata"))

        evaluations = []
        _evaluations = d.pop("evaluations")
        for evaluations_item_data in _evaluations:
            evaluations_item = EvaluationResult.from_dict(evaluations_item_data)

            evaluations.append(evaluations_item)

        co_occurring_issues = []
        _co_occurring_issues = d.pop("co_occurring_issues")
        for co_occurring_issues_item_data in _co_occurring_issues:
            co_occurring_issues_item = CoOccurringIssue.from_dict(
                co_occurring_issues_item_data
            )

            co_occurring_issues.append(co_occurring_issues_item)

        feed_sidebar = cls(
            timeline=timeline,
            ai_metadata=ai_metadata,
            evaluations=evaluations,
            co_occurring_issues=co_occurring_issues,
        )

        feed_sidebar.additional_properties = d
        return feed_sidebar

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
