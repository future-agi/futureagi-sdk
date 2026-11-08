"""Metadata and pickle support shared by the billing and budget status errors."""

from __future__ import annotations

from typing import Any


class _MetadataDetails:
    """Read-only field accessors for optional gateway ``error.metadata``.

    ``metadata`` preserves the entire object, including unknown keys; absent
    fields return None. Administrative cap metadata replaces payment metadata.
    """

    metadata: dict[str, Any]

    @property
    def required_usd(self) -> Any:
        """What the request needed, in USD."""
        return self.metadata.get("required_usd")

    @property
    def available_usd(self) -> Any:
        """What was available, in USD."""
        return self.metadata.get("available_usd")

    @property
    def limit_source(self) -> Any:
        """Which limit refused the request."""
        return self.metadata.get("limit_source")

    @property
    def remedy_hint(self) -> Any:
        """What the gateway suggests doing, e.g. ``"retry"``."""
        return self.metadata.get("remedy_hint")

    @property
    def scope(self) -> Any:
        """Whose credits or budget it was, e.g. the key, the agent or the organisation."""
        return self.metadata.get("scope")

    @property
    def resets_at(self) -> Any:
        """When the budget resets, as the gateway sent it."""
        return self.metadata.get("resets_at")

    @property
    def reason(self) -> Any:
        """The gateway's reason for the refusal."""
        return self.metadata.get("reason")

    @property
    def cap_scope(self) -> Any:
        """Administrative cap scope, when this producer sends it."""
        return self.metadata.get("cap_scope")

    @property
    def cap_ref(self) -> Any:
        """Administrative cap reference, when supplied."""
        return self.metadata.get("cap_ref")

    @property
    def cap_kind(self) -> Any:
        """Administrative cap kind, when supplied."""
        return self.metadata.get("cap_kind")

    @property
    def policy_revision(self) -> Any:
        """Administrative policy revision, when supplied."""
        return self.metadata.get("policy_revision")

    @property
    def suggestions(self) -> Any:
        """Eligible model suggestions, absent when the gateway supplies none."""
        return self.metadata.get("suggestions")

    @property
    def model_alias_requested(self) -> Any:
        """The requested model alias, when the routing refusal supplies it."""
        return self.metadata.get("model_alias_requested")


class _RefusalDetails:
    """Preserve the released billing/budget exception pickle representation."""

    args: tuple[Any, ...]

    def __reduce__(self) -> tuple[Any, ...]:
        from fi.gateway._exceptions import _rebuild_refusal

        # Never pickle the response: it holds the request and its headers.
        state = {k: v for k, v in vars(self).items() if k != "response"}
        state["response"] = None
        return (_rebuild_refusal, (type(self), self.args, state))
