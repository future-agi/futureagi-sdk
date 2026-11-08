"""Remove an unqualified connector sub-feature from the release source tree.

Run on a clean release copy. Generation removes methods and policy modules;
namespace OFF also removes root accessors and package exports, not just visibility.
"""
from __future__ import annotations

import argparse
import json
import re
import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def hide(feature: str) -> None:
    manifest = ROOT / "openapi/connectors/features.json"
    features = json.loads(manifest.read_text())
    if feature not in features:
        raise ValueError(f"Unknown connector feature: {feature}")
    features[feature] = False
    if feature == "mcp_core":
        features["oauth_connect"] = False
    if feature == "data_integrations":
        features["slack_channels"] = False
    manifest.write_text(json.dumps(features, indent=2) + "\n")
    if feature == "credential_reads":
        runpy.run_path(str(ROOT / "scripts/connectors/hide_platform_credentials.py"))["hide_platform_credentials"](ROOT)
        subprocess.run(["bash", str(ROOT / "scripts/generate-platform-sdk.sh")], check=True)
    subprocess.run(["node", str(ROOT / "scripts/connectors/generate.mjs")], check=True)
    namespaces = {"mcp_core": "connectors", "credential_reads": "credentials", "data_integrations": "integrations"}
    namespace = namespaces.get(feature)
    if namespace is None:
        return
    for file in ("futureagi_client.py", "futureagi_async_client.py"):
        target = ROOT / "python/fi" / file
        text = target.read_text()
        text, count = re.subn(r"    @property\n    def " + namespace + r"\(self\) -> Any:\n.*?(?=    @)", "", text, flags=re.S)
        if count != 1:
            raise ValueError(f"Expected exactly one {namespace} accessor in {file}")
        target.write_text(text)
    ts = ROOT / "typescript/futureagi/src/futureagi-client.ts"
    text = ts.read_text()
    cls = namespace.title()
    text = text.replace(f'import {{ {cls} }} from "./{namespace}";\n', "")
    text, count = re.subn(r"  /\*\* [^\n]+ \*/\n  get " + namespace + r"\(\): [^\n]+\n\n", "", text)
    if count != 1:
        raise ValueError(f"Expected exactly one TS {namespace} accessor")
    ts.write_text(text)
    package = ROOT / "typescript/futureagi/package.json"
    data = json.loads(package.read_text())
    data["exports"].pop(f"./{namespace}", None)
    data.get("typesVersions", {}).get("*", {}).pop(namespace, None)
    package.write_text(json.dumps(data, indent=2) + "\n")
    # Empty source directories are not namespace packages after this operation.
    for folder in (ROOT / "python/fi" / namespace, ROOT / "typescript/futureagi/src" / namespace):
        if folder.exists() and not any(folder.iterdir()):
            folder.rmdir()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature", choices=["mcp_core", "oauth_connect", "data_integrations", "slack_channels", "credential_reads"])
    hide(parser.parse_args().feature)
