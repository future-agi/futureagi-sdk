"""The binding contract (tests/platform-conformance/README.md "Bindings") for a stub Python SDK (test only)."""

import httpx

PACKAGE = {"name": "stub-client-py", "version": "0.0.0-stub"}
ROUTES = {
    ("platform", "capabilities.get"): lambda a: "/workspace/capabilities",
    ("sandboxes", "list"): lambda a: "/workspace/sandboxes",
    ("sandboxes", "getInfo"): lambda a: f"/workspace/sandboxes/{a['sandbox']}",
}
CLASSES = {
    400: "BadRequestError",
    401: "AuthenticationError",
    403: "PermissionDeniedError",
    404: "NotFoundError",
}


class StubStatusError(Exception):
    def __init__(self, status, code):
        super().__init__(f"stub {status} {code}")
        self.status = status
        self.code = code


def create_client(
    baseUrl, credential, fetch=None, options=None, transport=None, async_transport=None
):
    token = credential.get("apiKey") or credential.get("token")
    return httpx.Client(
        base_url=baseUrl,
        transport=transport,
        follow_redirects=False,
        headers={"authorization": f"Bearer {token}"},
    )


def call(client, sdk, args, **_):
    path = ROUTES[(sdk["family"], sdk["method"])](args)
    response = client.get(path)
    if response.status_code >= 400:
        body = response.json() if response.content else {}
        raise StubStatusError(
            response.status_code,
            body.get("code")
            or (body.get("error") or {}).get("code")
            or f"http_{response.status_code}",
        )
    return response.json()


def describe_error(error):
    if isinstance(error, StubStatusError):
        return {
            "errorClass": CLASSES.get(error.status, "APIStatusError"),
            "status": error.status,
            "code": error.code,
        }
    return {"errorClass": "SDKException"}
