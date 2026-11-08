"""Construct the FA executor without depending on legacy namespace modules."""
from typing import Any

from fi._core.fa_management import management_origin, scrub_management_value
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared, Settings
from fi._credentials import resolve
from fi.generated.platform.fa_management.policy import OPERATIONS


def get_core(client: Any, *, asynchronous: bool = False) -> Any:
    """Initialize and publish one parent-owned executor, including on Python 3.12."""
    with client._management_lock:
        # Publish before unlocking: cached_property itself does not synchronize
        # concurrent first reads on every supported Python version.
        if "_management" not in client.__dict__:
            client.__dict__["_management"] = make_core(client, asynchronous=asynchronous)
        return client.__dict__["_management"]


def make_core(client: Any, *, asynchronous: bool = False) -> Any:
    """Bind resolved FA credentials, selectors and defaults to the generated operation table."""
    options = client._options
    def origin():
        return management_origin(resolve(options.api_key, options.secret_key, client.base_url,
            workspace_id=options.workspace_id, organization_id=options.organization_id,
            platform_token=options.platform_token))
    shared = PlatformShared(origin, retries=options.retries, table=OPERATIONS,
                            extra_headers=client._extra_headers, error_scrubber=scrub_management_value)
    cls = AsyncPlatformCore if asynchronous else PlatformCore
    return cls(shared, Settings(timeout=options.timeout))
