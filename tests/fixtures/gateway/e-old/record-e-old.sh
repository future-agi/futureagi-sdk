#!/usr/bin/env bash
# Historical recorder entry point cited by the golden manifest.
# The combined recording requires a TypeScript recorder outside this repository.
printf '%s\n' 'Combined golden recording is unavailable in this repository. The committed recordings are in tests/fixtures/gateway/golden/.' >&2
exit 2
