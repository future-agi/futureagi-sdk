"""Managed run collections (async), using the shared platform executor."""
from __future__ import annotations

from fi.generated.platform import types as wire

from typing import Any, Optional
from fi._core.pagination import AsyncPage, alist_page
from ._handles._async_client import AsyncRun, _present


class AsyncRuns:
    """Run collection on the one platform client, with opaque cursor pagination."""

    def __init__(self, core: Any) -> None:
        self._core = core

    async def create(
        self,
        *,
        input: str,
        title: Optional[str] = None,
        mode: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_session_id: Optional[str] = None,
        model_id: Optional[str] = None,
        message_mode: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        wait: bool = False,
        timeout: float = 300.0,
    ) -> AsyncRun:
        """Create a run; optionally wait for done/error/canceled (timeout in seconds).

        waiting_approval is not terminal. A wait timeout does not cancel the created run;
        supply idempotency_key to recover it without starting a second run.
        """
        raw = await self._core.call(
            "runs.create",
            body={
                "input": input,
                **_present(
                    title=title,
                    mode=mode,
                    agentId=agent_id,
                    agentSessionId=agent_session_id,
                    modelId=model_id,
                    messageMode=message_mode,
                    attachments=attachments,
                    metadata=metadata,
                ),
            },
            idempotency_key=idempotency_key,
        )
        run = AsyncRun(self, raw)
        if wait:
            await run.wait(timeout=timeout)
        return run

    async def get(self, run_id: str) -> AsyncRun:
        """Fetch a run and its detail envelope."""
        return AsyncRun(self, await self._core.call("runs.get", path={"id": run_id}))

    async def delete(
        self, run_id: str
    ) -> wire.OmegaDeleteWorkspaceConversationsByIdResponse:
        """Delete one run, retaining the server's deletion receipt in the return value."""
        return await self._core.call("runs.delete", path={"id": run_id})

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        agent_version: Optional[int] = None,
        deployment_version: Optional[int] = None,
        channel_id: Optional[str] = None,
        provider_event_id: Optional[str] = None,
        external_correlation_id: Optional[str] = None,
    ) -> AsyncPage[AsyncRun]:
        """List matching runs; iterating the page fetches subsequent pages lazily."""
        return await alist_page(
            self._core,
            "runs.list",
            cursor=cursor,
            query=_present(
                limit=limit,
                agentId=agent_id,
                status=status,
                agentVersion=agent_version,
                deploymentVersion=deployment_version,
                channelId=channel_id,
                providerEventId=provider_event_id,
                externalCorrelationId=external_correlation_id,
            ),
            transform=lambda raw: AsyncRun(self, raw),
        )

    async def list_approvals(
        self,
        *,
        conversation_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> wire.OmegaGetWorkspaceApprovalsResponse:
        """Read pending or decided approvals; pass a decided response's nextCursor to continue."""
        return await self._core.call(
            "platform.approvals.list",
            query=_present(
                conversationId=conversation_id, state=state, limit=limit, cursor=cursor
            ),
        )


class AsyncRatings:
    """Read the caller's aggregate ratings. A signal is not a claim of learning."""

    def __init__(self, core: Any) -> None:
        self._core = core

    async def summary(self) -> wire.GetWorkspaceRatingsSummaryResponse:
        """Return latest-wins rating counts and satisfaction rate."""
        return await self._core.call("platform.ratings.summary")

    async def trajectory(self) -> wire.GetWorkspaceRatingsTrajectoryResponse:
        """Return the satisfaction time series exactly as reported by the server."""
        return await self._core.call("platform.ratings.trajectory")
