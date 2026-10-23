"""Create an API key + secret on a local Future AGI backend and write .env.local.

    python sdkgen/local_api_key.py --email you@example.com --password-file pw.txt
    # or FAGI_ADMIN_EMAIL / FAGI_ADMIN_PASSWORD in the environment

Uses the same endpoints the UI uses: POST /accounts/token/ (login), then
POST /accounts/key/generate_secret_key/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--email", default=os.environ.get("FAGI_ADMIN_EMAIL"))
    parser.add_argument("--password-file", help="file holding the password (keeps it off the command line)")
    args = parser.parse_args()
    password = Path(args.password_file).read_text().strip() if args.password_file else os.environ.get("FAGI_ADMIN_PASSWORD")
    if not args.email or not password:
        sys.exit("need --email and a password (--password-file or FAGI_ADMIN_PASSWORD)")

    with httpx.Client(base_url=args.base_url, timeout=60) as http:
        login = http.post("/accounts/token/", json={"email": args.email, "password": password})
        login.raise_for_status()
        access = login.json()["access"]
        created = http.post("/accounts/key/generate_secret_key/", json={"key_name": "sdk-poc"},
                            headers={"Authorization": f"Bearer {access}"})
        created.raise_for_status()
        result = created.json()["result"]

    env = ROOT / ".env.local"
    env.write_text(f"FI_BASE_URL={args.base_url}\nFI_API_KEY={result['api_key']}\nFI_SECRET_KEY={result['secret_key']}\n")
    env.chmod(0o600)
    print(f"wrote {env.relative_to(ROOT)} (key {result['masked_api_key']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
