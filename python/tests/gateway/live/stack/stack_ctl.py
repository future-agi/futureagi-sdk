"""Small helpers run-wire-suite.sh calls. Standard library only.

    python3 -I stack_ctl.py wait <url> <seconds>      exit 0 once GET <url> answers 200
    python3 -I stack_ctl.py secret <prefix>           print <prefix> + 32 random hex digits
    python3 -I stack_ctl.py sha12 <value>             print sha256(value)[:12]
    python3 -I stack_ctl.py mint <gateway> <out.json> write this run's virtual keys
    python3 -I stack_ctl.py org-config <gateway> <org> [cache|fallback]

``org-config`` PUTs an org config to ``/-/orgs/<org>/config``:

- ``cache`` (the default): ``{"cache": {"enabled": true, "default_ttl": 300}}``. At
  the recorded source the cache is opt-in per org (handlers.go applyOrgCacheOverrides), so a key
  without an org config never reads or fills it.
- ``fallback``: the org's own routing (tenant RoutingConfig): failover on 502 and 503,
  and the model fallback chain mock-fails -> gpt-4o-mini. At the
  pin a chain is tried only behind a failover (fallback_resolve.go shouldTryModelFallback),
  and the org's failover is used for that org's keys only (org_routing.go
  effectiveFailover), so the other orgs' error and deadline cases keep the gateway's own
  behaviour.

``mint`` writes the keys file (mode 0600) the suites read:

- ``plain`` and ``override``: the two keys gateway.yaml registers (``auth.keys``, type
  internal; the second with ``allow_policy_override``), made by run-wire-suite.sh for this
  run and read here from GW_LIVE_KEY_PLAIN / GW_LIVE_KEY_OVERRIDE.
- ``fallback``: the third key gateway.yaml registers (type internal, ``org_id``
  org-fallback, the org the ``fallback`` profile configures), read from GW_LIVE_KEY_FALLBACK.
- ``byok``: a key minted through the admin API (``POST /-/keys`` with the run's
  AGENTCC_ADMIN_TOKEN, ``org_id`` org-live). At the recorded source such a key is type byok: it may
  use only its org's own providers, never the config file's (handlers.go
  resolveProviderFor: "Non-internal keys must not resolve to global providers"), and
  test_live_core records that answer. An org provider of its own would serve it if it sat
  on a private address with AGENTCC_ALLOW_PRIVATE_PROVIDER_URLS=true and ``enabled: true``
  in its entry; the gateway refuses a loopback provider URL in every case, and this
  stack's mock is on loopback, so the suites use the internal keys above.

It prints only names, ids and key prefixes, never a key.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

MINTED = {"byok": {"name": "live-byok", "owner": "live-owner", "metadata": {"org_id": "org-live"}}}


def wait(url: str, seconds: float) -> int:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return 0
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    print(f"timed out waiting for {url}", file=sys.stderr)
    return 1


def mint(gateway: str, out: str) -> int:
    token = os.environ["AGENTCC_ADMIN_TOKEN"]
    result = {"plain": {"name": "live-plain", "key": os.environ["GW_LIVE_KEY_PLAIN"], "via": "gateway.yaml auth.keys"},
              "override": {"name": "live-override", "key": os.environ["GW_LIVE_KEY_OVERRIDE"],
                           "via": "gateway.yaml auth.keys"},
              "fallback": {"name": "live-fallback", "key": os.environ["GW_LIVE_KEY_FALLBACK"],
                           "via": "gateway.yaml auth.keys"}}
    for label, body in MINTED.items():
        req = urllib.request.Request(f"{gateway.rstrip('/')}/-/keys", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            created = json.loads(r.read())
        result[label] = {"id": created["id"], "key": created["key"], "name": created["name"], "via": "POST /-/keys",
                         "key_type": created.get("key_type")}
        print(f"minted {label}: id={created['id']} prefix={created.get('key_prefix')} status={created.get('status')}")
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(result, f)
    return 0


ORG_CONFIGS = {
    "cache": {"cache": {"enabled": True, "default_ttl": 300}},
    "fallback": {"routing": {"failover": {"enabled": True, "max_attempts": 2, "on_status_codes": [502, 503]},
                             "model_fallbacks": {"mock-fails": ["gpt-4o-mini"]}}},
}


def org_config(gateway: str, org: str, profile: str = "cache") -> int:
    body = ORG_CONFIGS[profile]
    req = urllib.request.Request(f"{gateway.rstrip('/')}/-/orgs/{org}/config", data=json.dumps(body).encode(),
                                 method="PUT", headers={"Authorization": f"Bearer {os.environ['AGENTCC_ADMIN_TOKEN']}",
                                                        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        print(f"org config {org}: {r.status} {r.read()[:200].decode(errors='replace')}")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1]
    if cmd == "wait":
        return wait(argv[2], float(argv[3]))
    if cmd == "secret":
        print(argv[2] + secrets.token_hex(16))
        return 0
    if cmd == "sha12":
        print(hashlib.sha256(argv[2].encode()).hexdigest()[:12])
        return 0
    if cmd == "mint":
        return mint(argv[2], argv[3])
    if cmd == "org-config":
        return org_config(argv[2], argv[3], *argv[4:5])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
