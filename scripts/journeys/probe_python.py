"""Run only inside a clean, disconnected installed-wheel consumer."""
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import sys

# -I excludes both the consumer working directory and this trusted tool directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from network import RuntimeGuard
from probe_common import Checks, demand, member, mock_backend, provision


def absence(checks, policy, root, clients):
    for namespace, spec in policy["surfaces"].items():
        if policy["states"][namespace]["py"] != "OFF":
            continue
        for module in spec["py_modules"]:
            fullname = "fi." + module
            def missing(fullname=fullname):
                try:
                    importlib.import_module(fullname)
                except ModuleNotFoundError as exc:
                    demand(exc.name == fullname or fullname.startswith(str(exc.name) + "."))
                else:
                    raise AssertionError("OFF module importable")
            checks.run("absence." + namespace + ".import." + fullname, missing)
        for path in spec["py_accessors"]:
            for client in clients:
                def missing_member(path=path, client=client):
                    try:
                        member(client, path)
                    except AttributeError:
                        return
                    raise AssertionError("OFF accessor present")
                checks.run("absence." + namespace + ".accessor." + type(client).__name__ + "." + path, missing_member)
        for module in spec["py_modules"]:
            if "." not in module:
                checks.run("absence." + namespace + ".root." + module,
                           lambda module=module: demand(not hasattr(root, module) and module not in getattr(root, "__all__", [])))
        for symbol in spec["root_exports"]:
            checks.run("absence." + namespace + ".root-export." + symbol,
                       lambda symbol=symbol: demand(symbol not in getattr(root, "__all__", []) and not hasattr(root, symbol)))
        def no_cli(namespace=namespace):
            distribution = metadata.distribution("futureagi")
            demand(not any(entry.group == "futureagi.cli" and entry.name == namespace
                           for entry in distribution.entry_points))
        checks.run("absence." + namespace + ".cli", no_cli)


def install_checks(checks, policy):
    root = importlib.import_module("fi")
    clients = []
    for symbol in ("FutureAGIClient", "AsyncFutureAGIClient"):
        checks.run("install.client." + symbol, lambda symbol=symbol: clients.append(getattr(root, symbol)()))
    for entry in policy["python_entries"]:
        def imported(entry=entry):
            module, _, symbol = entry.partition(":")
            obj = importlib.import_module(module)
            if symbol:
                getattr(obj, symbol)
        checks.run("install.import." + entry, imported)
    checks.run("install.no-fi-script", lambda: demand(shutil.which("fi") is None and not any(
        ep.name == "fi" for dist in metadata.distributions() for ep in dist.entry_points if ep.group == "console_scripts")))
    profile = os.environ.get("CONSUMER_EXTRA", "base")
    if profile != "base":
        checks.run("install.extra." + profile, lambda: demand(profile in metadata.metadata("futureagi").get_all("Provides-Extra", [])))
    def doctor():
        from installed_cli import futureagi
        saved = dict(os.environ)
        try:
            with mock_backend() as backend:
                pair = provision(backend)
                os.environ.update(FI_API_KEY=pair["api_key"], FI_SECRET_KEY=pair["secret_key"],
                                  FI_BASE_URL=backend.url, FI_PLATFORM_BASE_URL=backend.url + "/omega/api")
                child = None
                def invoke():
                    nonlocal child
                    child = futureagi('doctor', '--json')
                    demand(child.returncode == 0)
                checks.run("install.doctor-status", invoke)
                demand(child is not None and child.returncode == 0)
                result = json.loads(child.stdout)
                checks.run("install.doctor-identity", lambda: demand(bool(result.get("who", {}).get("user"))))
                # Doctor also probes each installed group's routes; those are
                # legitimate authenticated requests, not extra identity lookups.
                def headers():
                    demand(sum(r["path"] == "/accounts/user-info/" for r in backend.requests) == 1)
                    demand(all(r["headers"].get("x-api-key") == pair["api_key"] and
                               r["headers"].get("x-secret-key") == pair["secret_key"] and
                               not r["path"].startswith("/accounts/keys/") for r in backend.requests))
                checks.run("install.doctor-credential-headers", headers)
                checks.run("install.doctor-sections", lambda: demand(not any(
                    section.get("error") or section.get("problems") for section in result.get("sections", {}).values())))
        finally:
            os.environ.clear()
            os.environ.update(saved)
    checks.run("install.doctor-json", doctor)
    absence(checks, policy, root, clients)


def main():
    guard = RuntimeGuard()
    guard.install()
    policy = json.loads(Path(sys.argv[1]).read_text())
    checks = Checks()
    checks.run("install.probe", lambda: install_checks(checks, policy))
    if os.environ.get("CONSUMER_CONFIG") == "1":
        from config_python import check_config
        checks.run("config.probe", lambda: check_config(checks, policy))
    evidence = {"runtime": sys.version.split()[0], "checks": checks.rows, "network": guard.result()}
    Path(sys.argv[2]).write_text(json.dumps(evidence, indent=2) + "\n")
    return int(any(c["state"] == "FAIL" for c in checks.rows) or evidence["network"]["denied_count"] > 0)


if __name__ == "__main__":
    sys.exit(main())
