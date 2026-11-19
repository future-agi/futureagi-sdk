/** Observe queries use the one client; use traceAI packages for instrumentation. */
import { ConfigurationError } from "../_core/errors";
import { Dashboards } from "../generated/catalog/dashboards";
import { TracingQueries } from "../generated/tracing";

/** Query one bounded span page; preserve cursor and completeness metadata. */
export interface TraceSpanQuery extends Record<string, unknown> {
  project_id: string;
  filters?: ReadonlyArray<Record<string, unknown>>;
}

/** Observe queries and dashboard management share the root's authenticated transport. */
export class TracingClient extends TracingQueries {
  /** Dashboards, widgets and metrics on the same client pool. */
  get dashboards(): Dashboards {
    return new Dashboards(this.client, this.headers);
  }

  /** Scope to project and trace; additional filters are ANDed, never substituted. Pagination: page_number (0-based); page_size (page size); cursor (opaque continuation token); cursor_mode (enable cursor pagination). */
  spansByTrace(traceId: string, query: TraceSpanQuery) {
    if (typeof traceId !== "string" || !traceId.trim()) {
      throw new ConfigurationError("trace_id must be a non-empty string");
    }
    if (!query || typeof query.project_id !== "string" || !query.project_id.trim()) {
      throw new ConfigurationError("project_id must be a non-empty string");
    }
    const filters = query.filters ?? [];
    if (!Array.isArray(filters) || filters.some(item => item === null || typeof item !== "object" || Array.isArray(item))) {
      throw new ConfigurationError("filters must be a sequence of filter mappings");
    }
    const scoped = [...filters, { column_id: "trace_id", filter_config: {
      col_type: "SYSTEM_METRIC", filter_type: "text", filter_op: "in", filter_value: [traceId],
    } }];
    return this.spans({ ...query, filters: JSON.stringify(scoped) });
  }
}
