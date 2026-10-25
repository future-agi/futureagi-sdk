"""Files resource — file management with full AgentCC integration."""

from __future__ import annotations

from typing import Any

from fi.gateway._agentcc_params import (
    build_extra_headers,
    collect_agentcc_params,
    merge_session_headers,
)
from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.files import FileDeleted, FileList, FileObject


class Files:
    """Sync files resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        file: Any,
        purpose: str,
        # AgentCC-specific params
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileObject:
        agentcc_params = collect_agentcc_params(
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers, properties=properties,
            user_id=user_id, request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/files",
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        opts.body = {"purpose": purpose}
        opts.files = {"file": file}
        return self._client._get_base_client()._request_with_retry(opts, FileObject, agentcc_params)

    def list(
        self,
        *,
        purpose: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileList:
        from fi.gateway._utils import parse_timeout

        url = "/v1/files"
        if purpose is not None:
            url = f"/v1/files?purpose={purpose}"

        opts = RequestOptions(
            method="GET",
            url=url,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, FileList)

    def retrieve(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileObject:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/files/{file_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, FileObject)

    def content(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> bytes:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/files/{file_id}/content",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_raw_with_retry(opts)

    def delete(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileDeleted:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="DELETE",
            url=f"/v1/files/{file_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, FileDeleted)


class AsyncFiles:
    """Async files resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        file: Any,
        purpose: str,
        # AgentCC-specific params
        session_id: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        request_metadata: Any = NOT_GIVEN,
        properties: dict[str, str] | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileObject:
        agentcc_params = collect_agentcc_params(
            session_id=session_id, trace_id=trace_id,
            request_metadata=request_metadata,
        )

        extra_hdrs = build_extra_headers(
            extra_headers=extra_headers, properties=properties,
            user_id=user_id, request_id=request_id,
        )
        extra_hdrs = merge_session_headers(self._client, extra_hdrs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/files",
            headers=extra_hdrs,
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        opts.body = {"purpose": purpose}
        opts.files = {"file": file}
        return await self._client._get_base_client()._request_with_retry(opts, FileObject, agentcc_params)

    async def list(
        self,
        *,
        purpose: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileList:
        from fi.gateway._utils import parse_timeout

        url = "/v1/files"
        if purpose is not None:
            url = f"/v1/files?purpose={purpose}"

        opts = RequestOptions(
            method="GET",
            url=url,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, FileList)

    async def retrieve(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileObject:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/files/{file_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, FileObject)

    async def content(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> bytes:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="GET",
            url=f"/v1/files/{file_id}/content",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_raw_with_retry(opts)

    async def delete(
        self,
        file_id: str,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
    ) -> FileDeleted:
        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="DELETE",
            url=f"/v1/files/{file_id}",
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, FileDeleted)
