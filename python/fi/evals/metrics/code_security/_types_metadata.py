"""Metadata for types."""
from __future__ import annotations

from fi.evals.metrics.code_security.types import (Any, Dict, Severity)

CWE_METADATA: Dict[str, Dict[str, Any]] = {
    "CWE-89": {
        "name": "SQL Injection",
        "description": "Improper neutralization of special elements in SQL commands",
        "default_severity": Severity.HIGH,
        "owasp": "A03:2021",
    },
    "CWE-78": {
        "name": "OS Command Injection",
        "description": "Improper neutralization of special elements in OS commands",
        "default_severity": Severity.CRITICAL,
        "owasp": "A03:2021",
    },
    "CWE-79": {
        "name": "Cross-Site Scripting (XSS)",
        "description": "Improper neutralization of input during web page generation",
        "default_severity": Severity.MEDIUM,
        "owasp": "A03:2021",
    },
    "CWE-798": {
        "name": "Hardcoded Credentials",
        "description": "Use of hard-coded credentials",
        "default_severity": Severity.HIGH,
        "owasp": "A07:2021",
    },
    "CWE-22": {
        "name": "Path Traversal",
        "description": "Improper limitation of pathname to a restricted directory",
        "default_severity": Severity.HIGH,
        "owasp": "A01:2021",
    },
    "CWE-502": {
        "name": "Deserialization of Untrusted Data",
        "description": "Deserialization of untrusted data can result in code execution",
        "default_severity": Severity.CRITICAL,
        "owasp": "A08:2021",
    },
    "CWE-327": {
        "name": "Broken Cryptographic Algorithm",
        "description": "Use of a broken or risky cryptographic algorithm",
        "default_severity": Severity.MEDIUM,
        "owasp": "A02:2021",
    },
    "CWE-330": {
        "name": "Insufficient Randomness",
        "description": "Use of insufficiently random values",
        "default_severity": Severity.MEDIUM,
        "owasp": "A02:2021",
    },
    "CWE-287": {
        "name": "Improper Authentication",
        "description": "Improper authentication allowing unauthorized access",
        "default_severity": Severity.HIGH,
        "owasp": "A07:2021",
    },
    "CWE-306": {
        "name": "Missing Authentication",
        "description": "Missing authentication for critical function",
        "default_severity": Severity.HIGH,
        "owasp": "A07:2021",
    },
    "CWE-352": {
        "name": "Cross-Site Request Forgery (CSRF)",
        "description": "Cross-site request forgery vulnerability",
        "default_severity": Severity.MEDIUM,
        "owasp": "A01:2021",
    },
    "CWE-611": {
        "name": "XML External Entity (XXE)",
        "description": "Improper restriction of XML external entity reference",
        "default_severity": Severity.HIGH,
        "owasp": "A05:2021",
    },
    "CWE-918": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "Server-side request forgery",
        "default_severity": Severity.HIGH,
        "owasp": "A10:2021",
    },
    "CWE-434": {
        "name": "Unrestricted File Upload",
        "description": "Unrestricted upload of file with dangerous type",
        "default_severity": Severity.HIGH,
        "owasp": "A04:2021",
    },
    "CWE-20": {
        "name": "Improper Input Validation",
        "description": "Improper input validation",
        "default_severity": Severity.MEDIUM,
        "owasp": "A03:2021",
    },
    "CWE-120": {
        "name": "Buffer Overflow",
        "description": "Buffer copy without checking size of input",
        "default_severity": Severity.CRITICAL,
        "owasp": "A06:2021",
    },
    "CWE-476": {
        "name": "NULL Pointer Dereference",
        "description": "NULL pointer dereference",
        "default_severity": Severity.MEDIUM,
        "owasp": "A06:2021",
    },
    "CWE-190": {
        "name": "Integer Overflow",
        "description": "Integer overflow or wraparound",
        "default_severity": Severity.HIGH,
        "owasp": "A06:2021",
    },
    "CWE-209": {
        "name": "Information Exposure Through Error Message",
        "description": "Generation of error message containing sensitive information",
        "default_severity": Severity.LOW,
        "owasp": "A04:2021",
    },
    "CWE-400": {
        "name": "Resource Exhaustion",
        "description": "Uncontrolled resource consumption",
        "default_severity": Severity.MEDIUM,
        "owasp": "A05:2021",
    },
    "CWE-404": {
        "name": "Improper Resource Shutdown",
        "description": "Improper resource shutdown or release",
        "default_severity": Severity.LOW,
        "owasp": "A05:2021",
    },
    "CWE-259": {
        "name": "Hardcoded Password",
        "description": "Use of hard-coded password",
        "default_severity": Severity.HIGH,
        "owasp": "A07:2021",
    },
    "CWE-321": {
        "name": "Hardcoded Cryptographic Key",
        "description": "Use of hard-coded cryptographic key",
        "default_severity": Severity.HIGH,
        "owasp": "A02:2021",
    },
    "CWE-532": {
        "name": "Information Exposure Through Log Files",
        "description": "Insertion of sensitive information into log file",
        "default_severity": Severity.MEDIUM,
        "owasp": "A09:2021",
    },
}
