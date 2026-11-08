"""The Python case catalog, one module per catalog bullet.

``all_cases()`` returns every case in a fixed order; ids are unique and stable,
because goldens and ``catalog.json`` key on them.
"""

from __future__ import annotations

from .._runner import Case


def all_cases() -> list[Case]:
    from . import (
        config,
        config_legacy,
        envmatrix,
        headers,
        mocks,
        params,
        resources,
        response_headers,
        retry,
        statuses,
        streams,
        surface,
        utilities,
    )

    cases: list[Case] = []
    for module in (
        surface,
        resources,
        params,
        headers,
        config,
        config_legacy,
        response_headers,
        statuses,
        retry,
        streams,
        utilities,
        mocks,
        envmatrix,
    ):
        cases.extend(module.cases())
    ids = [c.id for c in cases]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate case ids: {duplicates}")
    return cases
