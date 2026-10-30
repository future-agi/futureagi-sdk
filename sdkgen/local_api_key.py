"""Get an API key + secret from a Future AGI backend and write .env.local.

Two ways in, same endpoints the UI uses:

    # an existing account (a local backend you installed yourself)
    python sdkgen/local_api_key.py --email you@example.com --password-file pw.txt
    # or FAGI_ADMIN_EMAIL / FAGI_ADMIN_PASSWORD in the environment

    # a fresh account on a throwaway stack (CI, the monorepo's E2E stack)
    python sdkgen/local_api_key.py --signup --base-url http://localhost:8100

--signup follows e2e/lib/provisioning.ts in the monorepo: POST /accounts/signup/,
POST /accounts/token/, GET /accounts/user-info/ until the default workspace exists,
GET /accounts/keys/ for the organization's system key. The login path calls
POST /accounts/token/ and POST /accounts/key/generate_secret_key/ instead.

The tests read .env.local (python/tests/platform/conftest.py, src/platform/__tests__/live.test.ts).
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def login_keys(http: httpx.Client, email: str, password: str) -> dict:
    login = http.post("/accounts/token/", json={"email": email, "password": password})
    login.raise_for_status()
    access = login.json()["access"]
    created = http.post(
        "/accounts/key/generate_secret_key/",
        json={"key_name": "sdk-local"},
        headers={"Authorization": f"Bearer {access}"},
    )
    created.raise_for_status()
    return created.json()["result"]


def signup_keys(http: httpx.Client, label: str) -> dict:
    # futureagi.com addresses skip the captcha the way the monorepo's E2E harness does.
    run_id = f"{int(time.time()):x}-{secrets.token_hex(3)}"
    email = f"sdk-e2e-{label}-{run_id}@futureagi.com"
    password = f"Sdk-e2e-{secrets.token_urlsafe(12)}"
    signup = http.post(
        "/accounts/signup/",
        json={"email": email, "full_name": f"SDK E2E {label}", "password": password, "company_name": "SDK E2E"},
    )
    if signup.status_code >= 400:
        sys.exit(f"signup failed ({signup.status_code}): {signup.text[:300]}")
    login = http.post("/accounts/token/", json={"email": email, "password": password, "remember_me": True})
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['access']}"}

    # The organization and its default workspace are created right after signup.
    deadline = time.monotonic() + 60
    while True:
        info = http.get("/accounts/user-info/", headers=headers)
        info.raise_for_status()
        body = info.json()
        organization_id = (body.get("organization") or {}).get("id")
        workspace_id = body.get("default_workspace_id")
        if organization_id and workspace_id:
            break
        if time.monotonic() > deadline:
            sys.exit(f"no default workspace for {email} after 60s: {body}")
        time.sleep(1)

    keys = http.get(
        "/accounts/keys/",
        headers={**headers, "X-Organization-Id": organization_id, "X-Workspace-Id": workspace_id},
    )
    keys.raise_for_status()
    data = keys.json()["data"]
    return {"api_key": data["api_key"], "secret_key": data["secret_key"], "masked_api_key": data["api_key"][:6] + "…", "email": email}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base-url", default=os.environ.get("FI_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--signup", action="store_true", help="create a fresh account instead of logging in")
    parser.add_argument("--label", default="ci", help="--signup: part of the generated email address")
    parser.add_argument("--email", default=os.environ.get("FAGI_ADMIN_EMAIL"))
    parser.add_argument("--password-file", help="file holding the password (keeps it off the command line)")
    parser.add_argument("--output", default=str(ROOT / ".env.local"), help="env file to write")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=60) as http:
        if args.signup:
            result = signup_keys(http, args.label)
        else:
            password = Path(args.password_file).read_text().strip() if args.password_file else os.environ.get("FAGI_ADMIN_PASSWORD")
            if not args.email or not password:
                sys.exit("need --email and a password (--password-file or FAGI_ADMIN_PASSWORD), or --signup")
            result = login_keys(http, args.email, password)

    env = Path(args.output)
    env.write_text(f"FI_BASE_URL={args.base_url}\nFI_API_KEY={result['api_key']}\nFI_SECRET_KEY={result['secret_key']}\n")
    env.chmod(0o600)
    who = f" as {result['email']}" if "email" in result else ""
    print(f"wrote {env} (key {result['masked_api_key']}){who}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
