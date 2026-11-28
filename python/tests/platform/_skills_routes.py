"""Whether the product under test serves the Skills routes (shared by conftest and the live suite)."""

from __future__ import annotations

SKILLS_OPERATION_PREFIXES = ("contexts.", "skill_consumption.", "context_credentials.", "skills.")
SKILLS_PROBE = "/model-hub/skills/"
_SKILLS_SERVED: list[bool] = []


def skills_served_by(client) -> bool:
    """Whether the product serves the Skills routes. False only when GET /model-hub/skills/ answers
    404 with Django's own HTML page, which a missing route gets. A JSON error body means a
    Skills view answered, so the routes exist; any other failure propagates and fails the run."""
    from fi.platform import APIError

    try:
        client.request("GET", SKILLS_PROBE)
    except APIError as exc:
        html = "text/html" in exc.response.headers.get("content-type", "")
        if exc.status_code == 404 and html and not isinstance(exc.body, (dict, list)):
            return False
        if exc.status_code == 404:
            raise AssertionError(f"GET {SKILLS_PROBE} answered a 404 that is not Django's page: {exc.body!r}") from exc
        return True  # e.g. a JSON 403 for a workspace without the feature: the Skills tests then fail
    return True


def skills_served(client) -> bool:
    if not _SKILLS_SERVED:
        _SKILLS_SERVED.append(skills_served_by(client))
    return _SKILLS_SERVED[0]
