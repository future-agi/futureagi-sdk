"""Clean Docker consumers on a VM; installation has registry-only proxy access."""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import uuid

from network import RegistryProxy
from container_network import ContainerNetwork


class Consumers:
    def __init__(self, kit, output):
        self.kit, self.output = Path(kit).resolve(), Path(output).resolve()
        self.sequence = 0
        self.images = {}
        self.steps = []
        self.observers = {}
        self.observations = {}
        self.proxy = RegistryProxy()
        self.network = "consumer-matrix-" + uuid.uuid4().hex[:10]

    def command(self, name, argv, required=True):
        self.sequence += 1
        log = self.output / "logs" / f"{self.sequence:03}-{name}.log"
        log.parent.mkdir(exist_ok=True)
        print("START", name, flush=True)
        with log.open("w") as stream:
            try:
                result = subprocess.run(list(map(str, argv)), stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
        self.steps.append({"name": name, "exit": code, "log": str(log.relative_to(self.output))})
        (self.output / "steps.json").write_text(json.dumps(self.steps, indent=2))
        print("END", name, code, flush=True)
        if required and code:
            raise RuntimeError(name + " failed; inspect step log")
        return code

    def __enter__(self):
        self.command("observer-image", ["docker", "build", "--tag", "consumer-network-observer", "--file",
                                        self.kit / "observer.Dockerfile", self.kit])
        self.observer_image = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}",
                                                      "consumer-network-observer"], text=True).strip()
        self.images["network-observer"] = self.observer_image
        self.command("private-network", ["docker", "network", "create", "--internal", self.network])
        data = json.loads(subprocess.check_output(["docker", "network", "inspect", self.network]))[0]
        self.gateway = data["IPAM"]["Config"][0]["Gateway"]
        self.proxy.__enter__()
        return self

    def __exit__(self, *args):
        self.proxy.__exit__(*args)
        self.command("remove-network", ["docker", "network", "rm", self.network], required=False)

    def image(self, tag):
        if tag not in self.images:
            self.command("image-pull", ["docker", "pull", tag])
            data = json.loads(subprocess.check_output(["docker", "image", "inspect", tag]))[0]
            self.images[tag] = data["RepoDigests"][0]
        return self.images[tag]

    @contextmanager
    def container(self, tag, artifact, policy, result, config, extra="base"):
        name = "consumer-" + uuid.uuid4().hex[:12]
        result.mkdir()
        result.chmod(0o777)
        proxy = f"http://{self.gateway}:{self.proxy.port}"
        observer = ContainerNetwork(self.output / (name + '-control'), result, self.output / (name + '.trace'),
                                    (self.gateway, self.proxy.port))
        command = ["docker", "run", "--detach", "--name", name, "--network", self.network,
                   "--cpus", "4", "--memory", "8g", "--pids-limit", "256", "--cap-drop=ALL",
                   "--security-opt=no-new-privileges"]
        for source, target, readonly in ((self.kit, "/kit", True), (artifact, "/input/" + artifact.name, True),
                                         (policy, "/input/policy.json", True), (result, "/result", False),
                                         (observer.control, "/control", True)):
            command += ["--mount", f"type=bind,source={source.resolve()},target={target}" + (",readonly" if readonly else "")]
        for value in ("CI=1", "PYTHONDONTWRITEBYTECODE=1", "PIP_DISABLE_PIP_VERSION_CHECK=1",
                      "LITELLM_LOCAL_MODEL_COST_MAP=True", "HOME=/tmp/consumer-home", "FI_LOGIN_FILE=/tmp/consumer-home/login.json",
                      "FI_AGENT_CODE_ENABLED=1", f"CONSUMER_EXTRA={extra}", f"CONSUMER_CONFIG={int(config)}",
                      f"HTTPS_PROXY={proxy}", f"HTTP_PROXY={proxy}", "NO_PROXY=127.0.0.1,localhost,::1",
                      "FI_BASE_URL=http://127.0.0.1:9", "FI_PLATFORM_BASE_URL=http://127.0.0.1:9/omega/api"):
            command += ["--env", value]
        try:
            self.command("container-start", [*command, self.image(tag), "sh", "/kit/supervisor.sh"])
            data = json.loads(subprocess.check_output(["docker", "inspect", name]))[0]
            observer.start(data["State"]["Pid"], self.observer_image)
            self.observers[name] = observer
            yield name, proxy
        finally:
            self.command("container-remove", ["docker", "rm", "--force", name], required=False)
            try:
                self.observations[name] = observer.finish()
            except Exception as exc:
                self.observations[name] = {"denied_count": 0, "complete": False, "error": type(exc).__name__}
            (self.output / "container-network.json").write_text(json.dumps(self.observations, indent=2))

    def execute(self, box, name, argv, required=True, cwd="/"):
        # No candidate code is executed through docker exec, which would escape
        # PID 1's descendant trace. All commands use the read-only supervisor queue.
        self.sequence += 1
        log = self.output / "logs" / f"{self.sequence:03}-{name}.log"
        print("START", name, flush=True)
        code = self.observers[box].execute(self.sequence, argv, cwd, log)
        self.steps.append({"name": name, "exit": code, "log": str(log.relative_to(self.output))})
        (self.output / "steps.json").write_text(json.dumps(self.steps, indent=2))
        print("END", name, code, flush=True)
        if required and code:
            raise RuntimeError(name + " failed; inspect step log")
        return code

    def offline(self, box):
        self.command("network-disconnect", ["docker", "network", "disconnect", self.network, box])
        data = json.loads(subprocess.check_output(["docker", "inspect", box]))[0]
        if data["NetworkSettings"]["Networks"]:
            raise RuntimeError("Consumer still has an external interface")
        self.observers[box].offline()

    def python(self, version, extra, artifact, policy, config):
        label = "py-" + version + "-" + extra
        out = self.output / label
        with self.container(f"python:{version}-slim-bookworm", artifact, policy, out, config, extra) as (box, proxy):
            # Real-container startup smoke before any installation or matrix loop.
            self.execute(box, "python-startup", ["python", "-I", "-c", "import json, pathlib; assert pathlib.Path('/kit/probe_python.py').is_file()"])
            target = "/input/" + artifact.name + ("[" + extra + "]" if extra != "base" else "")
            code = self.execute(box, "python-install", ["python", "-I", "-m", "pip", "install", "--only-binary=:all:", "--proxy", proxy, "--index-url", "https://pypi.org/simple", target], False)
            self.offline(box)
            if code:
                return label, {"checks": [{"name": "install.dependencies", "state": "FAIL", "reason": "Wheel installation failed"}], "network": {"denied_count": 0}}
            dependency_code = self.execute(box, "python-dependencies", ["python", "-I", "-m", "pip", "check"], False)
            self.execute(box, "python-probe", ["python", "-I", "/kit/probe_python.py", "/input/policy.json", "/result/probe.json"], False)
            result = json.loads((out / "probe.json").read_text())
            result["checks"].append({"name": "install.dependency-consistency", "state": "FAIL" if dependency_code else "PASS"})
            return label, result

    def node(self, version, artifact, policy, config):
        label = "ts-" + version
        out = self.output / label
        with self.container(f"node:{version}-bookworm-slim", artifact, policy, out, config) as (box, proxy):
            self.execute(box, "node-startup", ["node", "-e", "require('node:fs').accessSync('/kit/probe_node.cjs')"])
            self.execute(box, "node-init", ["sh", "-ec", "mkdir /consumer; printf '{\"name\":\"matrix-consumer\",\"private\":true}' > /consumer/package.json; cp /kit/probe_node.cjs /consumer/probe.cjs"])
            code = self.execute(box, "node-install", ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org", "--proxy=" + proxy, "--https-proxy=" + proxy, "/input/" + artifact.name], False, "/consumer")
            self.offline(box)
            if code:
                return label, {"checks": [{"name": "install.dependencies", "state": "FAIL", "reason": "Tarball installation failed"}], "network": {"denied_count": 0}}
            dependency_code = self.execute(box, "node-dependencies", ["npm", "ls", "--omit=dev"], False, "/consumer")
            self.execute(box, "node-probe", ["node", "probe.cjs", "/input/policy.json", "/result/probe.json"], False, "/consumer")
            result = json.loads((out / "probe.json").read_text())
            result["checks"].append({"name": "install.dependency-consistency", "state": "FAIL" if dependency_code else "PASS"})
            return label, result
