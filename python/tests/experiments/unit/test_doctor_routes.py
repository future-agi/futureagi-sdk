"""doctor's experiments section checks the routes an uploaded run needs (one GET each, on an id that
cannot exist). No network: MockTransport."""

import httpx

from fi.experiments._cli import routes


def _client(handler):
    from fi.futureagi_client import FutureAGIClient

    c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
    c.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
    return c


def test_json_answers_mean_present_and_an_html_404_means_missing():
    def handler(request):
        if "external-metrics" in request.url.path:
            return httpx.Response(404, text="<html>Not Found</html>", headers={"content-type": "text/html"})
        if request.url.path == "/model-hub/experiment-runs/":
            return httpx.Response(405, json={"detail": "Method GET not allowed."})
        return httpx.Response(404, json={"status": False, "message": "not found"})

    lines = routes.route_lines(_client(handler))
    platform_lines = [line for line in lines if "collector" not in line.lower()]
    assert len(platform_lines) == len(routes.ROUTES)
    assert any("SRV-5 external metrics" in line and "MISSING" in line for line in platform_lines)
    assert sum("present" in line for line in platform_lines) == len(routes.ROUTES) - 1


def test_refused_keys_and_offline_and_no_keys():
    lines = routes.route_lines(_client(lambda r: httpx.Response(401, json={"detail": "no"})))
    assert all("keys refused" in line for line in lines)

    class Args:
        offline = True

    assert routes.doctor_route_lines(Args()) == ["Routes     not checked (--offline)"]
    Args.offline = False
    assert "no keys" in routes.doctor_route_lines(Args())[0]
