"""
Injection Vulnerability Detectors.

Detects various injection vulnerabilities:
- CWE-89: SQL Injection
- CWE-78: OS Command Injection
- CWE-79: Cross-Site Scripting (XSS)
- CWE-94: Code Injection
- CWE-611: XXE Injection
- CWE-918: SSRF
"""

import re
from typing import List, Optional, Dict, Set

from .base import BaseDetector, PatternBasedDetector, register_detector
from ..types import (
    SecurityFinding,
    Severity,
    VulnerabilityCategory,
)
from ..analyzer import AnalysisResult


from ._injection_s_q_l_injection_detector_detect import _SQLInjectionDetectorDetectMethods

from ._injection_sqlinjection import SQLInjectionDetector
SQLInjectionDetector.__module__ = __name__


from ._injection_command_injection_detector_detect import _CommandInjectionDetectorDetectMethods

from ._injection_commandinjection import CommandInjectionDetector
CommandInjectionDetector.__module__ = __name__


from ._injection_xss import XSSDetector
XSSDetector.__module__ = __name__


from ._injection_codeinjection import CodeInjectionDetector
CodeInjectionDetector.__module__ = __name__


from ._injection_xxe import XXEDetector
XXEDetector.__module__ = __name__


from ._injection_ssrf import SSRFDetector
SSRFDetector.__module__ = __name__


from ._injection_pathtraversal import PathTraversalDetector
PathTraversalDetector.__module__ = __name__


# Export all detectors
__all__ = [
    "SQLInjectionDetector",
    "CommandInjectionDetector",
    "XSSDetector",
    "CodeInjectionDetector",
    "XXEDetector",
    "SSRFDetector",
    "PathTraversalDetector",
]
