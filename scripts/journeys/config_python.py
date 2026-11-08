"""Installed Python credential checks against the loopback personal-key fixture."""
import importlib
import json
import os
from pathlib import Path
from installed_cli import futureagi
from probe_common import demand, member, mock_backend, provision, refused


def check_config(checks, policy):
    from fi import FutureAGIClient

    with mock_backend() as server:
        pair = provision(server)
        os.environ.update(FI_API_KEY=pair["api_key"], FI_SECRET_KEY=pair["secret_key"],
                          FI_BASE_URL=server.url, FI_PLATFORM_BASE_URL=server.url + "/omega/api")
        # Execute the installed command as a child of the traced supervisor.
        def cli_login():
            child = futureagi('login', '--from-env')
            demand(child.returncode == 0)
            saved = json.loads(Path(os.environ["FI_LOGIN_FILE"]).read_text())
            demand(saved["api_key"] == pair["api_key"] and saved["secret_key"] == pair["secret_key"])
            demand(Path(os.environ["FI_LOGIN_FILE"]).stat().st_mode & 0o777 == 0o600)
        checks.run("config.login-from-env", cli_login)
        client = FutureAGIClient()

        def request(path, args=(), receiver=client):
            before = len(server.requests)
            member(receiver, path)(*args)
            received = server.requests[before:]
            demand(len(received) == 1)
            headers = received[0]["headers"]
            demand(headers.get("x-api-key") == pair["api_key"] and headers.get("x-secret-key") == pair["secret_key"])
            demand("authorization" not in headers)
        checks.run("config.default-client", lambda: request("users.current"))
        checks.run("config.platform-origin-headers", lambda: request("_platform.call", ["platform.capabilities.get"]))
        for call in policy["config_calls"]["py"]:
            checks.run("config.namespace." + call["path"], lambda call=call: request(call["path"], call.get("args", [])))

        if policy["states"]["webhooks"]["py"] == "ON":
            def webhook_request():
                from fi.webhooks import Webhooks
                wh = Webhooks()
                try:
                    request("endpoints.list", receiver=wh)
                finally:
                    wh.close()
            checks.run("config.namespace.webhooks", webhook_request)

        def saved_login():
            del os.environ["FI_API_KEY"]
            del os.environ["FI_SECRET_KEY"]
            try:
                saved_client = FutureAGIClient()
                before = len(server.requests)
                saved_client.users.current()
                demand(len(server.requests) == before + 1)
                demand(server.requests[-1]["headers"].get("x-api-key") == pair["api_key"])
                saved_client.close()
            finally:
                os.environ.update(FI_API_KEY=pair["api_key"], FI_SECRET_KEY=pair["secret_key"])
        checks.run("config.saved-login", saved_login)

        def preflight(options):
            # Traverse the real operation executor: a resolver-only assertion
            # would miss a transport that bypassed credential validation.
            c = FutureAGIClient(**options)
            try:
                c._platform.call("platform.capabilities.get")
            finally:
                c.close()
        before = len(server.requests)
        checks.run("config.mixed-credentials", lambda: refused(
            lambda: preflight({"platform_token": "fixture-selfhost-token"}), {"MixedCredentialsError"}))
        checks.run("config.unsafe-origin", lambda: refused(
            lambda: preflight({"platform_base_url": "https://untrusted.invalid/omega/api"}), {"HostNotAllowedError"}))
        def incomplete_pair():
            c = FutureAGIClient(api_key=pair["api_key"], base_url=server.url)
            try:
                refused(lambda: c.users.current(), {"MissingAuthError", "CredentialsMissingError"})
            finally:
                c.close()
        checks.run("config.no-mixed-key-sources", incomplete_pair)
        checks.run("config.negatives-no-request", lambda: demand(len(server.requests) == before))

        def precedence():
            os.environ.update(FI_API_KEY="conflicting-fixture-api", FI_SECRET_KEY="conflicting-fixture-secret")
            explicit = None
            try:
                explicit = FutureAGIClient(api_key=pair["api_key"], secret_key=pair["secret_key"], base_url=server.url)
                before = len(server.requests)
                explicit.users.current()
                demand(len(server.requests) == before + 1)
                headers = server.requests[-1]["headers"]
                demand(headers.get("x-api-key") == pair["api_key"] and headers.get("x-secret-key") == pair["secret_key"])
            finally:
                os.environ.update(FI_API_KEY=pair["api_key"], FI_SECRET_KEY=pair["secret_key"])
                if explicit is not None:
                    explicit.close()
        checks.run("config.argument-precedence", precedence)

        if policy["states"]["gateway"]["py"] == "ON":
            def fi_refusal():
                from fi.gateway import AgentCC
                for key in (pair["api_key"], pair["secret_key"]):
                    refused(lambda: AgentCC(api_key=key, base_url=server.url), {"AgentCCError"})
            checks.run("config.fi-pair-not-gateway", fi_refusal)
        else:
            checks.skip("config.fi-pair-not-gateway", "Gateway data-plane namespace OFF; absence checked separately")
        if policy["states"]["gateway_management"]["py"] == "ON":
            def virtual_refusal():
                before = len(server.requests)
                c = FutureAGIClient(api_key="sk-agentcc-fixture-only", secret_key="fixture-only", base_url=server.url)
                refused(lambda: c.gateway.config.get_active(), {"ConfigurationError", "AuthError", "CredentialsMissingError", "AuthenticationError"})
                demand(len(server.requests) == before)
                c.close()
            checks.run("config.virtual-key-not-management", virtual_refusal)
        else:
            checks.skip("config.virtual-key-not-management", "Gateway management namespace OFF; absence checked separately")
        checks.run("config.no-retired-key-route", lambda: demand(not any(r["path"].startswith("/accounts/keys/") for r in server.requests)))
        client.close()
