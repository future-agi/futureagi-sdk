#!/usr/bin/env python3
"""Fail closed unless release bytes match the source's reviewed manifest."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


# Deliberately not configurable by arguments, environment, or build output.
MANIFEST = Path(__file__).resolve().parents[1] / "cleared-release-artifacts.json"
TAG = re.compile(r"(python|typescript)-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))")
DIGEST = re.compile(r"[0-9a-f]{64}")
CLEARANCE_REQUIRED = (
    "New bytes need independent security clearance; "
    "do not update the manifest automatically."
)


def expected_names(tag):
    match = TAG.fullmatch(tag)
    if match is None:
        raise ValueError("unsupported release tag")
    ecosystem, version = match.groups()
    if ecosystem == "python":
        return {f"futureagi-{version}-py3-none-any.whl", f"futureagi-{version}.tar.gz"}
    return {f"future-agi-sdk-{version}.tgz"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result


def open_regular(filename, *, directory_fd=None):
    # O_NONBLOCK prevents a FIFO from hanging before fstat rejects it.
    descriptor = os.open(
        filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
        dir_fd=directory_fd,
    )
    stream = os.fdopen(descriptor, "rb")
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        stream.close()
        raise ValueError("artifact or manifest is not a regular file")
    return stream


def reviewed_releases():
    with open_regular(MANIFEST) as source:
        document = json.loads(source.read(), object_pairs_hook=unique_object)
    if not isinstance(document, dict) or set(document) != {"schema_version", "releases"}:
        raise ValueError("invalid manifest structure")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("unsupported manifest schema version")
    releases = document["releases"]
    if not isinstance(releases, dict) or not releases:
        raise ValueError("manifest has no reviewed releases")
    for tag, artifacts in releases.items():
        # Deriving the exact allowed basenames also excludes path traversal,
        # absolute paths, wrong versions, and additional metadata/files.
        names = expected_names(tag)
        if not isinstance(artifacts, dict) or set(artifacts) != names:
            raise ValueError("manifest must name exactly the release's artifacts")
        if any(not isinstance(digest, str) or DIGEST.fullmatch(digest) is None
               for digest in artifacts.values()):
            raise ValueError("manifest contains an invalid or absent SHA-256 digest")
    return releases


def verify_release(tag, directory):
    expected_names(tag)
    releases = reviewed_releases()
    if tag not in releases:
        raise ValueError("release tag has no independent artifact clearance")
    artifacts = releases[tag]
    directory = Path(directory)
    # Pin the directory while checking its exact inventory and opening files;
    # neither a symlink directory nor a symlink artifact is accepted.
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if set(os.listdir(directory_fd)) != set(artifacts):
            raise ValueError("distribution directory has missing or unexpected files")
        for name, expected_digest in artifacts.items():
            digest = hashlib.sha256()
            with open_regular(name, directory_fd=directory_fd) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected_digest:
                raise ValueError(f"SHA-256 mismatch for {name}")
    finally:
        os.close(directory_fd)
    return tuple(directory / name for name in sorted(artifacts))


def require_unpublished(tag):
    expected_names(tag)
    ecosystem, version = tag.split("-v", 1)
    if ecosystem == "python":
        url = f"https://pypi.org/pypi/futureagi/{version}/json"
    else:
        url = f"https://registry.npmjs.org/%40future-agi%2Fsdk/{version}"
    try:
        with urlopen(url, timeout=30):
            pass
    except HTTPError as error:
        if error.code == 404:
            return
        raise ValueError("registry absence could not be established; publication stopped") from error
    except (URLError, OSError) as error:
        raise ValueError("registry absence could not be established; publication stopped") from error
    raise ValueError(
        "release version already exists; independent registry readback is required "
        "before deciding what to do next; do not reupload or automatically retry"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--require-unpublished", action="store_true")
    args = parser.parse_args(argv)
    try:
        verified = verify_release(args.tag, args.directory)
        if args.require_unpublished:
            require_unpublished(args.tag)
    except (ValueError, OSError) as error:
        print(f"Artifact clearance failed: {error}. {CLEARANCE_REQUIRED}", file=sys.stderr)
        return 1
    print(f"Verified {len(verified)} cleared artifacts for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
