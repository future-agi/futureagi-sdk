from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.trace_agent_graph_result_query_status import (
    TraceAgentGraphResultQueryStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_agent_graph_edge import TraceAgentGraphEdge
    from ..models.trace_agent_graph_node import TraceAgentGraphNode


T = TypeVar("T", bound="TraceAgentGraphResult")


@_attrs_define
class TraceAgentGraphResult:
    """
    Attributes:
        nodes (list[TraceAgentGraphNode]):
        edges (list[TraceAgentGraphEdge]):
        path_edges (list[TraceAgentGraphEdge]):
        graph_collapsed (bool | Unset):
        graph_node_limit (int | Unset):
        omitted_node_count (int | Unset):
        query_complete (bool | Unset):
        query_status (TraceAgentGraphResultQueryStatus | Unset):
        query_sampled (bool | Unset):
        query_count (int | Unset):
        query_rows_returned (int | Unset):
        query_elapsed_ms (float | Unset):
        query_completed_at (datetime.datetime | Unset):
        query_cached (bool | Unset):
        query_refresh_failed (bool | Unset):
        query_refreshing (bool | Unset):
    """

    nodes: list[TraceAgentGraphNode]
    edges: list[TraceAgentGraphEdge]
    path_edges: list[TraceAgentGraphEdge]
    graph_collapsed: bool | Unset = UNSET
    graph_node_limit: int | Unset = UNSET
    omitted_node_count: int | Unset = UNSET
    query_complete: bool | Unset = UNSET
    query_status: TraceAgentGraphResultQueryStatus | Unset = UNSET
    query_sampled: bool | Unset = UNSET
    query_count: int | Unset = UNSET
    query_rows_returned: int | Unset = UNSET
    query_elapsed_ms: float | Unset = UNSET
    query_completed_at: datetime.datetime | Unset = UNSET
    query_cached: bool | Unset = UNSET
    query_refresh_failed: bool | Unset = UNSET
    query_refreshing: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        nodes = []
        for nodes_item_data in self.nodes:
            nodes_item = nodes_item_data.to_dict()
            nodes.append(nodes_item)

        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        path_edges = []
        for path_edges_item_data in self.path_edges:
            path_edges_item = path_edges_item_data.to_dict()
            path_edges.append(path_edges_item)

        graph_collapsed = self.graph_collapsed

        graph_node_limit = self.graph_node_limit

        omitted_node_count = self.omitted_node_count

        query_complete = self.query_complete

        query_status: str | Unset = UNSET
        if not isinstance(self.query_status, Unset):
            query_status = self.query_status.value

        query_sampled = self.query_sampled

        query_count = self.query_count

        query_rows_returned = self.query_rows_returned

        query_elapsed_ms = self.query_elapsed_ms

        query_completed_at: str | Unset = UNSET
        if not isinstance(self.query_completed_at, Unset):
            query_completed_at = self.query_completed_at.isoformat()

        query_cached = self.query_cached

        query_refresh_failed = self.query_refresh_failed

        query_refreshing = self.query_refreshing

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "nodes": nodes,
                "edges": edges,
                "path_edges": path_edges,
            }
        )
        if graph_collapsed is not UNSET:
            field_dict["graph_collapsed"] = graph_collapsed
        if graph_node_limit is not UNSET:
            field_dict["graph_node_limit"] = graph_node_limit
        if omitted_node_count is not UNSET:
            field_dict["omitted_node_count"] = omitted_node_count
        if query_complete is not UNSET:
            field_dict["query_complete"] = query_complete
        if query_status is not UNSET:
            field_dict["query_status"] = query_status
        if query_sampled is not UNSET:
            field_dict["query_sampled"] = query_sampled
        if query_count is not UNSET:
            field_dict["query_count"] = query_count
        if query_rows_returned is not UNSET:
            field_dict["query_rows_returned"] = query_rows_returned
        if query_elapsed_ms is not UNSET:
            field_dict["query_elapsed_ms"] = query_elapsed_ms
        if query_completed_at is not UNSET:
            field_dict["query_completed_at"] = query_completed_at
        if query_cached is not UNSET:
            field_dict["query_cached"] = query_cached
        if query_refresh_failed is not UNSET:
            field_dict["query_refresh_failed"] = query_refresh_failed
        if query_refreshing is not UNSET:
            field_dict["query_refreshing"] = query_refreshing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_agent_graph_edge import TraceAgentGraphEdge
        from ..models.trace_agent_graph_node import TraceAgentGraphNode

        d = dict(src_dict)
        nodes = []
        _nodes = d.pop("nodes")
        for nodes_item_data in _nodes:
            nodes_item = TraceAgentGraphNode.from_dict(nodes_item_data)

            nodes.append(nodes_item)

        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = TraceAgentGraphEdge.from_dict(edges_item_data)

            edges.append(edges_item)

        path_edges = []
        _path_edges = d.pop("path_edges")
        for path_edges_item_data in _path_edges:
            path_edges_item = TraceAgentGraphEdge.from_dict(path_edges_item_data)

            path_edges.append(path_edges_item)

        graph_collapsed = d.pop("graph_collapsed", UNSET)

        graph_node_limit = d.pop("graph_node_limit", UNSET)

        omitted_node_count = d.pop("omitted_node_count", UNSET)

        query_complete = d.pop("query_complete", UNSET)

        _query_status = d.pop("query_status", UNSET)
        query_status: TraceAgentGraphResultQueryStatus | Unset
        if isinstance(_query_status, Unset):
            query_status = UNSET
        else:
            query_status = TraceAgentGraphResultQueryStatus(_query_status)

        query_sampled = d.pop("query_sampled", UNSET)

        query_count = d.pop("query_count", UNSET)

        query_rows_returned = d.pop("query_rows_returned", UNSET)

        query_elapsed_ms = d.pop("query_elapsed_ms", UNSET)

        _query_completed_at = d.pop("query_completed_at", UNSET)
        query_completed_at: datetime.datetime | Unset
        if isinstance(_query_completed_at, Unset):
            query_completed_at = UNSET
        else:
            query_completed_at = isoparse(_query_completed_at)

        query_cached = d.pop("query_cached", UNSET)

        query_refresh_failed = d.pop("query_refresh_failed", UNSET)

        query_refreshing = d.pop("query_refreshing", UNSET)

        trace_agent_graph_result = cls(
            nodes=nodes,
            edges=edges,
            path_edges=path_edges,
            graph_collapsed=graph_collapsed,
            graph_node_limit=graph_node_limit,
            omitted_node_count=omitted_node_count,
            query_complete=query_complete,
            query_status=query_status,
            query_sampled=query_sampled,
            query_count=query_count,
            query_rows_returned=query_rows_returned,
            query_elapsed_ms=query_elapsed_ms,
            query_completed_at=query_completed_at,
            query_cached=query_cached,
            query_refresh_failed=query_refresh_failed,
            query_refreshing=query_refreshing,
        )

        trace_agent_graph_result.additional_properties = d
        return trace_agent_graph_result

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
