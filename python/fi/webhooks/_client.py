"""``Webhooks`` and ``AsyncWebhooks``: the webhooks REST API from code.

The namespaces below are written once. Each method builds request specs (``fi.webhooks._api``) and hands them to the
client's ``_send``, which runs them in order and returns the last result: the sync client returns it, the async client
returns an awaitable (``await wh.endpoints.list()``).

Keys and server come from ``fi._credentials`` (arguments, ``FI_API_KEY`` / ``FI_SECRET_KEY`` / ``FI_BASE_URL``, then
the saved ``futureagi-py login``; saved keys never go to a ``FI_BASE_URL`` they were not saved for). ``FI_EXTRA_HEADERS``
and ``extra_headers=`` (which wins per name) go on every request to that server, never to a receiver or another host
(``fi._extra_headers``). Redirects are never followed. Retries follow ``fi._http``: reads retry on 429, 502-504 and
network errors; writes only on 429 and before anything was sent.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import httpx

from fi._credentials import Credentials
from fi._credentials import resolve as resolve_credentials
from fi._extra_headers import ExtraHeaders
from fi._http import DEFAULT_TIMEOUT, AsyncRetryingTransport, LazyKeyAuth, RetryingTransport
from fi.webhooks import _api
from fi.webhooks._api import Call, When

_SETTINGS = ("timeout_ms", "rate_limit_per_s", "max_in_flight", "max_age_s")


def _endpoint_body(
    *,
    url=None,
    events=None,
    filters=None,
    name=None,
    description=None,
    headers=None,
    payload=None,
    include_people_names=None,
    accepts_run_targeting=None,
    timeout_s=None,
    rate_limit_per_s=None,
    max_in_flight=None,
    max_age=None,
    secret=None,
    **extra: Any,
) -> dict:
    body: dict = {
        "url": url,
        "subscriptions": _api.subscriptions(events, filters),
        "name": name,
        "description": description,
        "headers": headers,
        "payload_mode": payload,
        "include_people_names": include_people_names,
        "accepts_run_targeting": accepts_run_targeting,
        "timeout_ms": None if timeout_s is None else int(float(timeout_s) * 1000),
        "rate_limit_per_s": rate_limit_per_s,
        "max_in_flight": max_in_flight,
        "max_age_s": None if max_age is None else _api.seconds(max_age),
        "secret": secret,
    }
    body = {k: v for k, v in body.items() if v is not None}
    body.update(extra)
    return body


class _Endpoints:
    def __init__(self, client: "_Base") -> None:
        self._c = client

    def list(self, *, workspace=None, event_type=None, status=None, kind=None):
        """Endpoints the caller may see (``list[Endpoint]``), org-wide ones included. A read: retried."""
        return self._c._send(_api.list_endpoints(workspace=workspace, event_type=event_type, status=status, kind=kind))

    def create(
        self,
        *,
        url: str,
        events: Sequence[str],
        name: Optional[str] = None,
        filters: Optional[Mapping[str, Mapping[str, Any]]] = None,
        headers: Optional[Mapping[str, str]] = None,
        payload: Optional[str] = None,
        include_people_names: Optional[bool] = None,
        accepts_run_targeting: Optional[bool] = None,
        workspace_id: Any = ...,
        org_wide: bool = False,
        description: Optional[str] = None,
        timeout_s: Optional[float] = None,
        rate_limit_per_s: Optional[int] = None,
        max_in_flight: Optional[int] = None,
        max_age: Any = None,
        secret: Optional[str] = None,
    ):
        """Create an endpoint. The result is the :class:`Endpoint` plus ``secret`` (``whsec_...``, returned this once)
        and ``warnings``. ``name`` defaults to the URL's host. ``org_wide=True`` makes it receive every workspace's
        events (org admins). Header values are sent literally. One attempt: a write is never retried after a 5xx."""
        body = _endpoint_body(
            url=url,
            events=events,
            filters=filters,
            name=name or httpx.URL(url).host or url,
            description=description,
            headers=headers,
            payload=payload,
            include_people_names=include_people_names,
            accepts_run_targeting=accepts_run_targeting,
            timeout_s=timeout_s,
            rate_limit_per_s=rate_limit_per_s,
            max_in_flight=max_in_flight,
            max_age=max_age,
            secret=secret,
        )
        if org_wide:
            body["workspace_id"] = None
        elif workspace_id is not ...:
            body["workspace_id"] = None if workspace_id is None else str(workspace_id)
        return self._c._send(_api.create_endpoint(body))

    def get(self, endpoint_id):
        """One endpoint, never its secret. A read: retried."""
        return self._c._send(_api.get_endpoint(endpoint_id))

    def update(self, endpoint_id, *, clear_headers: bool = False, **changes: Any):
        """Change an endpoint: the keyword arguments of :meth:`create` (``events`` with ``filters`` replace every
        subscription; ``headers`` replaces the static headers; ``clear_headers=True`` removes them)."""
        body = _endpoint_body(**changes)
        if clear_headers:
            if "headers" in body:
                raise ValueError("pass headers= or clear_headers=True, not both")
            body["headers"] = None
        if not body:
            raise ValueError("nothing to update")
        return self._c._send(_api.update_endpoint(endpoint_id, body))

    def delete(self, endpoint_id):
        """Delete an endpoint: its secrets are destroyed at once and waiting deliveries are cancelled."""
        return self._c._send(_api.delete_endpoint(endpoint_id))

    def enable(self, endpoint_id, *, reason: Optional[str] = None, resume: Optional[str] = None):
        """Turn an endpoint on. ``resume="send"`` then delivers its paused backlog, ``"skip"`` drops it (audited).

        Returns the :class:`Endpoint` when ``resume`` is ``None``. With ``resume``, it returns the resume answer instead
        (``mode``, ``sent``, ``skipped``, ``past_max_age``, ``backlog_capped``), the same as :meth:`resume`; call
        :meth:`get` for the endpoint."""
        calls = [_api.toggle(endpoint_id, True, reason)]
        if resume is not None:
            calls.append(_api.resume(endpoint_id, resume))
        return self._c._send(*calls)

    def disable(self, endpoint_id, *, reason: Optional[str] = None):
        """Turn an endpoint off; new events wait as paused deliveries (up to 10,000)."""
        return self._c._send(_api.toggle(endpoint_id, False, reason))

    def resume(self, endpoint_id, mode: str):
        """Deliver (``"send"``) or skip (``"skip"``) the paused deliveries of an endpoint that is on."""
        return self._c._send(_api.resume(endpoint_id, mode))

    def rotate_secret(self, endpoint_id, *, overlap: Any = None, secret: Optional[str] = None):
        """A new active secret (:class:`Rotation`; ``secret`` is shown this once). The old one keeps verifying for
        ``overlap`` (default 24 h, ``"0s"`` to ``"7d"``; 0 revokes it at once)."""
        return self._c._send(_api.rotate_secret(endpoint_id, overlap, secret))

    def revoke_previous_secret(self, endpoint_id):
        """End a rotation overlap now: only the newest secret verifies from here on."""
        return self._c._send(_api.revoke_previous_secret(endpoint_id))

    def test(self, endpoint_id, *, event_type: str):
        """Send a signed test event of ``event_type`` from the delivery worker (:class:`TestResult`). The server waits
        up to 20 s; if the attempt has not settled by then, ``settled`` is False and ``delivery_id`` names it."""
        return self._c._send(_api.test(endpoint_id, event_type))

    test.__test__ = False  # type: ignore[attr-defined]


class _Deliveries:
    def __init__(self, client: "_Base") -> None:
        self._c = client

    def list(
        self,
        *,
        endpoint=None,
        status=None,
        event_type=None,
        event=None,
        subject=None,
        since: When = None,
        until: When = None,
        seq_from=None,
        seq_to=None,
        include_body=None,
        cursor=None,
        limit=None,
    ):
        """One :class:`Page` of the delivery log, newest first. ``since`` / ``until`` take a datetime, an ISO string or
        a duration ago (``"24h"``); ``seq_from=seq_to=N`` fetches sequence N of one endpoint."""
        return self._c._send(
            _api.list_deliveries(
                endpoint=endpoint,
                status=status,
                event_type=event_type,
                event=event,
                subject=subject,
                since=since,
                until=until,
                seq_from=seq_from,
                seq_to=seq_to,
                include_body=include_body,
                cursor=cursor,
                limit=limit,
            )
        )

    def get(self, delivery_id, *, attempts: bool = True):
        """One delivery with its ``attempts`` timeline (``attempts=False`` leaves the timeline out)."""
        return self._c._send(_api.get_delivery(delivery_id, attempts=attempts))

    def redeliver(self, delivery_id):
        """Queue one delivery again: same event id and body, a new attempt with a fresh timestamp and signature."""
        return self._c._send(_api.redeliver(delivery_id))

    def redeliver_many(self, *, endpoint, status, event_type=None, since: When = None, until: When = None,
                       dry_run: bool = False):
        """Queue every delivery of one endpoint matching the filter (at most 1,000). ``dry_run=True`` only counts."""
        return self._c._send(
            _api.redeliver_many(
                endpoint=endpoint, status=status, event_type=event_type, since=since, until=until, dry_run=dry_run
            )
        )


class _Events:
    def __init__(self, client: "_Base") -> None:
        self._c = client

    def list(self, *, type=None, subject=None, since: When = None, until: When = None, cursor=None, limit=None):
        """The events list for reconciliation (thin data, within the log retention), one :class:`Page`."""
        return self._c._send(
            _api.list_events(type=type, subject=subject, since=since, until=until, cursor=cursor, limit=limit)
        )


class _Policy:
    def __init__(self, client: "_Base") -> None:
        self._c = client

    def get(self, *, workspace=None):
        """The org policy, or a workspace's (allowed hosts, ``members_can_manage``, and the effective values)."""
        return self._c._send(_api.get_policy(workspace))

    def update(self, *, workspace=None, **changes: Any):
        """Replace policy fields (``allowed_hosts``, ``members_can_manage``; org: also ``full_payload_allowed``,
        ``log_retention_days``, ``max_endpoints_per_workspace``)."""
        return self._c._send(_api.put_policy(changes, workspace))


class _Base:
    """What both clients share: credentials, the namespaces and the response handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: Any = None,
        retries: int = 3,
        extra_headers: Optional[Mapping[str, str] | str] = None,
    ) -> None:
        creds = resolve_credentials(api_key, secret_key, base_url, workspace_id=workspace_id)
        self.base_url = creds.base_url
        # FI_EXTRA_HEADERS, extra_headers= winning per name: on requests to base_url only (fi._extra_headers)
        self._extra_headers = ExtraHeaders(self.base_url, extra_headers)
        self.workspace_id = creds.workspace_id
        self._timeout = DEFAULT_TIMEOUT if timeout is None else timeout
        self._retries = retries

        def _keys() -> Credentials:
            return resolve_credentials(api_key, secret_key, self.base_url, workspace_id=workspace_id)

        self._auth = LazyKeyAuth(_keys, extra=self._extra_headers)
        self.endpoints = _Endpoints(self)
        self.deliveries = _Deliveries(self)
        self.events = _Events(self)
        self.policy = _Policy(self)

    def _headers(self) -> dict:
        import fi

        out = {"User-Agent": f"futureagi-python/{fi.__version__} webhooks", "Accept": "application/json"}
        if self.workspace_id:
            out["X-Workspace-Id"] = str(self.workspace_id)
        return out

    @staticmethod
    def _result(call: Call, response: httpx.Response) -> Any:
        try:
            payload = response.json() if response.content else None
        except ValueError:
            payload = response.text[:2000]
        if response.status_code not in call.ok:
            raise _api.error(response.status_code, payload, response.headers)
        out = _api.unwrap(call, response.status_code, payload)
        return out

    def event_types(self):
        """The event catalog: each type's description, filters and JSON Schema (``results``, ``groups``,
        ``shared_schemas``)."""
        return self._send(_api.event_types())

    def egress_ips(self):
        """The published egress addresses webhook requests come from, per region (empty where none are published)."""
        return self._send(_api.egress_ips())

    def preview(self, *, event_type: str, payload: Optional[str] = None, include_people_names: Optional[bool] = None,
                headers: Optional[Mapping[str, str]] = None):
        """The exact request a receiver would get for a sample of ``event_type`` (signature and header values
        masked). No network call to any receiver."""
        body = {"event_type": event_type, "payload_mode": payload, "include_people_names": include_people_names,
                "headers": headers}
        return self._send(_api.preview({k: v for k, v in body.items() if v is not None}))

    def _send(self, *calls: Call) -> Any:  # pragma: no cover - each client defines it
        raise NotImplementedError


class Webhooks(_Base):
    """The webhooks API, synchronously. ``with Webhooks() as wh: ...`` closes the connection pool on exit.

    ``transport`` replaces the network layer under the SDK's retries (an ``httpx.MockTransport`` in tests)."""

    def __init__(self, *args: Any, transport: Optional[httpx.BaseTransport] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.Client(
            base_url=self.base_url,
            auth=self._auth,
            timeout=self._timeout,
            transport=RetryingTransport(transport, retries=self._retries),
            follow_redirects=False,
            headers=self._headers(),
        )

    def _send(self, *calls: Call) -> Any:
        out = None
        for call in calls:
            response = self._http.request(call.method, call.path, params=call.params or None, json=call.json)
            out = self._result(call, response)
        return out

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Webhooks":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class AsyncWebhooks(_Base):
    """The webhooks API for asyncio: the same namespaces and methods as :class:`Webhooks`, each awaited."""

    def __init__(self, *args: Any, transport: Optional[httpx.AsyncBaseTransport] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self._auth,
            timeout=self._timeout,
            transport=AsyncRetryingTransport(transport, retries=self._retries),
            follow_redirects=False,
            headers=self._headers(),
        )

    async def _send(self, *calls: Call) -> Any:
        out = None
        for call in calls:
            response = await self._http.request(call.method, call.path, params=call.params or None, json=call.json)
            out = self._result(call, response)
        return out

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncWebhooks":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()
