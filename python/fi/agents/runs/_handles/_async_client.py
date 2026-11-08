"""Managed run handles and collections (async); credentials and policy come from the client."""
from __future__ import annotations

from fi.generated.platform import types as wire

from typing import Any, AsyncIterator, Mapping, Optional

from fi._core.handles import AsyncHandle, apoll_until
from fi._core.resumable import StreamBounds, resumable_events
from fi.errors import ConfigurationError

_FINAL = frozenset(("done", "error", "canceled"))


def _present(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _sequence(after: Optional[int | str]) -> Optional[str]:
    if after is None:
        return None
    value = str(after)
    if (
        not value.isascii()
        or not value.isdigit()
        or (len(value) > 1 and value[0] == "0")
    ):
        raise ConfigurationError(
            "after must be a canonical non-negative event sequence",
            code="invalid_sequence",
        )
    return value


class AsyncRunRating:
    """Read, set or clear the caller's rating; no idempotency key is sent."""

    def __init__(self, core: Any, run_id: str) -> None:
        self._core, self._id = core, run_id

    async def get(self) -> wire.GetConversationRatingsResponse:
        """Return the current latest-wins ratings, including the server envelope."""
        return await self._core.call("runs.rating.get", path={"id": self._id})

    async def set(
        self, *, rating: Optional[str], message_id: Optional[str] = None
    ) -> wire.RecordConversationRatingResponse:
        """Set 'up' or 'down', or clear with None; optionally target one message."""
        if rating not in (None, "up", "down"):
            raise ConfigurationError(
                "rating must be 'up', 'down' or None", code="invalid_rating"
            )
        return await self._core.call(
            "runs.rating.set",
            path={"id": self._id},
            body={"rating": rating, **_present(messageId=message_id)},
        )


class AsyncRun(AsyncHandle):
    """A run is one multi-turn conversation with an agent.

    refresh/wait re-read the snapshot; a context cancels a nonterminal run on exit.

    data holds the conversation, response preserves the entire last read/create envelope.
    Errors, receipts and unknown server fields are never discarded. Approval decisions remain
    human-only. Leaving an events iterator closes its connection, not the run.
    """

    noun = "run"

    def __init__(self, namespace: Any, response: Mapping[str, Any]) -> None:
        data = response.get("conversation", response)
        if (
            not isinstance(data, Mapping)
            or not isinstance(data.get("id"), str)
            or not data["id"]
        ):
            raise ConfigurationError(
                "run response has no conversation id", code="invalid_run_response"
            )
        super().__init__(namespace, data)
        object.__setattr__(self, "_response", dict(response))
        object.__setattr__(self, "_snapshot_stale", False)

    @property
    def response(self) -> dict[str, Any]:
        """The unmodified last read/create envelope, including messages and receipts."""
        return self._response

    @property
    def identity(self) -> Any:
        """The server-stamped managed execution identity, when present."""
        return self.data.get("managedExecution")

    @property
    def rating(self) -> AsyncRunRating:
        """Ratings belonging to this run and caller."""
        return AsyncRunRating(self._ns._core, self.id)

    async def _get(self) -> Mapping[str, Any]:
        fresh = await self._ns.get(self.id)
        object.__setattr__(self, "_response", fresh.response)
        object.__setattr__(self, "_snapshot_stale", False)
        return fresh.data

    def _is_done(self) -> bool:
        return not self._snapshot_stale and self.status in _FINAL

    def events(
        self,
        *,
        after: Optional[int | str] = None,
        bounds: Optional[StreamBounds] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Resume strictly after a durable sequence, with bounded reconnects and idle timeout.

        Stop at the contract's done frame, not a status frame: later receipts may still follow.
        Close the iterator explicitly if abandoning it early.
        """
        return resumable_events(
            self._ns._core,
            "runs.events",
            path={"id": self.id},
            last_event_id=_sequence(after),
            bounds=bounds,
            is_end=lambda event: event.get("type") == "done",
        )

    async def send(
        self,
        *,
        input: str,
        model_id: Optional[str] = None,
        mode: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
        idempotency_key: Optional[str] = None,
    ) -> wire.OmegaPostWorkspaceConversationsByIdMessagesResponse | wire.OmegaPostWorkspaceConversationsByIdMessagesResponse2:
        """Send a turn with a replay key; wait re-reads completion after acceptance."""
        receipt = await self._ns._core.call(
            "runs.send",
            path={"id": self.id},
            body={
                "input": input,
                **_present(modelId=model_id, mode=mode, attachments=attachments),
            },
            idempotency_key=idempotency_key,
        )
        # Keep the last server snapshot intact, but do not use it to finish a new turn.
        object.__setattr__(self, "_snapshot_stale", True)
        return receipt

    async def cancel(self) -> wire.OmegaRunCancelResult:
        """Request cancellation and return its receipt; refresh to observe the result."""
        return await self._ns._core.call("runs.cancel", path={"id": self.id})

    async def interrupt(self) -> wire.InterruptWorkspaceConversationResponse:
        """Park this run without destroying it; this mutation is not retried after sending."""
        return await self._ns._core.call("runs.interrupt", path={"id": self.id})

    async def resume(
        self, *, idempotency_key: Optional[str] = None
    ) -> wire.ContinueWorkspaceConversationResponse:
        """Continue with a replay key; wait re-reads completion after acceptance."""
        receipt = await self._ns._core.call(
            "runs.continue", path={"id": self.id}, idempotency_key=idempotency_key
        )
        object.__setattr__(self, "_snapshot_stale", True)
        return receipt

    async def retry(
        self,
        *,
        reason: Optional[str] = None,
        category: Optional[str] = None,
        actor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> wire.RetryWorkspaceConversationResponse:
        """Retry with audit attribution; wait re-reads completion after acceptance."""
        receipt = await self._ns._core.call(
            "runs.retry",
            path={"id": self.id},
            body=_present(reason=reason, category=category, actor=actor),
            idempotency_key=idempotency_key,
        )
        object.__setattr__(self, "_snapshot_stale", True)
        return receipt

    async def fork(
        self,
        *,
        up_to_message_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> AsyncRun:
        """Copy the transcript into a new run; an omitted cut point copies all messages."""
        raw = await self._ns._core.call(
            "runs.fork",
            path={"id": self.id},
            body=_present(upToMessageId=up_to_message_id),
            idempotency_key=idempotency_key,
        )
        return AsyncRun(self._ns, raw)

    async def tree(self) -> wire.GetWorkspaceConversationTaskTreeResponse:
        """Return the canonical task-tree snapshot."""
        return await self._ns._core.call("runs.tree", path={"id": self.id})

    async def observations(
        self,
        *,
        task_id: Optional[str] = None,
        kind: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> wire.GetWorkspaceConversationObservationsResponse:
        """Return the observation window, preserving its truncated flag and metadata."""
        return await self._ns._core.call(
            "runs.observations",
            path={"id": self.id},
            query=_present(taskId=task_id, kind=kind, limit=limit),
        )

    async def evidence(self) -> wire.OmegaGetWorkspaceConversationsByIdEvidenceResponse:
        """Return the durable filesystem and browser evidence manifest."""
        return await self._ns._core.call("runs.evidence", path={"id": self.id})

    async def proof_pack(
        self,
    ) -> wire.OmegaGetWorkspaceConversationsByIdProofPackResponse:
        """Return the portable evidence bundle without changing or interpreting it."""
        return await self._ns._core.call("runs.proofPack", path={"id": self.id})

    async def control_status(self) -> wire.OmegaRunControlStatus:
        """Return phase, spend and process state, preserving null/unpriced values."""
        return await self._ns._core.call("runs.controlStatus", path={"id": self.id})

    async def approvals(
        self,
    ) -> wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse:
        """Read pending approvals; this SDK never decides them."""
        return await self._ns._core.call("runs.approvals", path={"id": self.id})

    async def wait_for_approval(
        self, *, timeout: float = 300.0
    ) -> wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse:
        """Wait for a nonempty approvals response without approving anything."""

        async def check() -> Optional[
            wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse
        ]:
            raw = await self.approvals()
            return raw if raw.get("approvals") else None

        return await apoll_until(check, timeout=timeout, label="waiting for approval")

    async def __aenter__(self) -> AsyncRun:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        # The snapshot may be stale; never assume a formerly active run still needs canceling.
        await self.refresh()
        if not self._is_done():
            await self.cancel()
