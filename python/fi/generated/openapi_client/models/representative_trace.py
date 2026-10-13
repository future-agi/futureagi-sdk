from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.agent_flow_graph import AgentFlowGraph
    from ..models.representative_trace_recommendations_item import (
        RepresentativeTraceRecommendationsItem,
    )
    from ..models.representative_trace_root_causes_item import (
        RepresentativeTraceRootCausesItem,
    )
    from ..models.representative_trace_what_changed import (
        RepresentativeTraceWhatChanged,
    )
    from ..models.trace_evidence import TraceEvidence
    from ..models.trace_summary import TraceSummary


T = TypeVar("T", bound="RepresentativeTrace")


@_attrs_define
class RepresentativeTrace:
    """
    Attributes:
        id (str):
        status (str):
        timestamp (datetime.datetime | None):
        summary (TraceSummary):
        evidence (TraceEvidence):
        agent_flow (AgentFlowGraph):
        root_causes (list[RepresentativeTraceRootCausesItem]):
        recommendations (list[RepresentativeTraceRecommendationsItem]):
        what_changed (RepresentativeTraceWhatChanged):
    """

    id: str
    status: str
    timestamp: datetime.datetime | None
    summary: TraceSummary
    evidence: TraceEvidence
    agent_flow: AgentFlowGraph
    root_causes: list[RepresentativeTraceRootCausesItem]
    recommendations: list[RepresentativeTraceRecommendationsItem]
    what_changed: RepresentativeTraceWhatChanged
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status = self.status

        timestamp: None | str
        if isinstance(self.timestamp, datetime.datetime):
            timestamp = self.timestamp.isoformat()
        else:
            timestamp = self.timestamp

        summary = self.summary.to_dict()

        evidence = self.evidence.to_dict()

        agent_flow = self.agent_flow.to_dict()

        root_causes = []
        for root_causes_item_data in self.root_causes:
            root_causes_item = root_causes_item_data.to_dict()
            root_causes.append(root_causes_item)

        recommendations = []
        for recommendations_item_data in self.recommendations:
            recommendations_item = recommendations_item_data.to_dict()
            recommendations.append(recommendations_item)

        what_changed = self.what_changed.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
                "timestamp": timestamp,
                "summary": summary,
                "evidence": evidence,
                "agent_flow": agent_flow,
                "root_causes": root_causes,
                "recommendations": recommendations,
                "what_changed": what_changed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_flow_graph import AgentFlowGraph
        from ..models.representative_trace_recommendations_item import (
            RepresentativeTraceRecommendationsItem,
        )
        from ..models.representative_trace_root_causes_item import (
            RepresentativeTraceRootCausesItem,
        )
        from ..models.representative_trace_what_changed import (
            RepresentativeTraceWhatChanged,
        )
        from ..models.trace_evidence import TraceEvidence
        from ..models.trace_summary import TraceSummary

        d = dict(src_dict)
        id = d.pop("id")

        status = d.pop("status")

        def _parse_timestamp(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timestamp_type_0 = isoparse(data)

                return timestamp_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        timestamp = _parse_timestamp(d.pop("timestamp"))

        summary = TraceSummary.from_dict(d.pop("summary"))

        evidence = TraceEvidence.from_dict(d.pop("evidence"))

        agent_flow = AgentFlowGraph.from_dict(d.pop("agent_flow"))

        root_causes = []
        _root_causes = d.pop("root_causes")
        for root_causes_item_data in _root_causes:
            root_causes_item = RepresentativeTraceRootCausesItem.from_dict(
                root_causes_item_data
            )

            root_causes.append(root_causes_item)

        recommendations = []
        _recommendations = d.pop("recommendations")
        for recommendations_item_data in _recommendations:
            recommendations_item = RepresentativeTraceRecommendationsItem.from_dict(
                recommendations_item_data
            )

            recommendations.append(recommendations_item)

        what_changed = RepresentativeTraceWhatChanged.from_dict(d.pop("what_changed"))

        representative_trace = cls(
            id=id,
            status=status,
            timestamp=timestamp,
            summary=summary,
            evidence=evidence,
            agent_flow=agent_flow,
            root_causes=root_causes,
            recommendations=recommendations,
            what_changed=what_changed,
        )

        representative_trace.additional_properties = d
        return representative_trace

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
