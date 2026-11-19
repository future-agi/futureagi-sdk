# Security Policy

## Reporting a vulnerability

The Future AGI team takes security seriously. If you discover a vulnerability in `futureagi-sdk`, please report it privately — **do not open a public GitHub issue.**

**Email:** **security@futureagi.com**

Include as much of the following as you can:

- Type of issue (e.g. dependency confusion, code injection via prompt template, credential leak in logs)
- Affected version(s) and the commit or release tag
- Reproduction steps
- Proof-of-concept or exploit code, if possible
- Impact — how an attacker might exploit it

## Response timeline

- **Acknowledgement:** within 24 hours (Mon–Fri, Pacific & IST)
- **Initial assessment:** within 3 business days
- **Fix target:** depends on severity
- **Public disclosure:** coordinated with the reporter, typically 7–90 days after a patch is available

## Scope

**In scope:**

- The `futureagi` PyPI package
- This repository's source (`future-agi/futureagi-sdk`)

**Out of scope:**

- Third-party LLM providers reached via API calls (report upstream)
- Upstream dependencies — report to those projects directly
- Prompts, datasets, or knowledge base content users feed into the SDK (user-controlled input)

For vulnerabilities that affect the broader Future AGI platform, see the [main repo's SECURITY.md](https://github.com/future-agi/future-agi/blob/main/SECURITY.md).

## Gateway credential masking

The Python gateway client sends the real authentication and client-composed header
values to the configured destination. After each request attempt, it masks those
values in retained requests, responses, SDK errors and their diagnostic causes,
and callback arguments that expose the completed exchange. SDK logging callbacks
omit credential-bearing request fields and use the sanitized error diagnostics.
Credential-named response headers are masked; ordinary gateway response headers
remain available. Masking does not erase caller-owned configuration or copies a
caller makes while a request is in flight, and is not a substitute for choosing a
trusted destination and using TLS.

Normal operation includes the SDK's own HTTP objects, supported HTTPX built-in
authentication, retry and redirect handling, event hooks, and SDK log records and
extra fields. Known exchange headers must be masked independently of optional
graph discovery. If inspection of normal diagnostic data cannot finish, that data
must be masked or replaced with a categorical marker rather than exposed raw.

This is an object-data and output boundary, not protection against code executing
inside the Python interpreter. Frame locals, traceback-frame inspection, garbage
collector inspection and closure contents are outside the guarantee. A formatted
SDK exception must not disclose client-composed credential values; inspecting the
frame objects behind its traceback is a different, excluded operation.

Objects or subclasses that a caller constructs and injects into the client or its
HTTP layer are scrubbed on a best-effort basis. In particular, custom descriptors,
attribute-name objects, exception rendering, caller-authored authentication or
stream implementations, mutated HTTPX internals, and deliberately deep or wide
object graphs may fall outside safe bounded inspection. The scrubber must not run
caller code or replace the original failure while attempting inspection. Do not
put credentials into these custom diagnostic objects, arbitrary log extras or
custom output sinks, and do not rely on the scrubber to erase independently held
copies of sensitive data.
