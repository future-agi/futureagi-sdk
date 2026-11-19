from enum import Enum


class ObserveGraphDataErrorResultQueryProvenance(str, Enum):
    BOUNDED_CANDIDATES = "bounded_candidates"
    EXACT_SNAPSHOT = "exact_snapshot"
    MATERIALIZED_ROLLUP = "materialized_rollup"

    def __str__(self) -> str:
        return str(self.value)
