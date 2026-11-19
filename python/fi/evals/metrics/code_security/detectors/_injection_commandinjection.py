"""Commandinjection for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    BaseDetector, Severity, VulnerabilityCategory, _CommandInjectionDetectorDetectMethods,
    register_detector,
)

@register_detector("command_injection")
class CommandInjectionDetector(_CommandInjectionDetectorDetectMethods, BaseDetector):
    """
    Detects OS command injection vulnerabilities (CWE-78).

    Identifies:
    - os.system() with variable input
    - subprocess with shell=True
    - eval/exec with user input
    - Backtick execution

    Examples of vulnerable code:
        os.system("ping " + host)
        subprocess.call(cmd, shell=True)
        eval(user_input)
    """

    name = "command_injection"
    cwe_ids = ["CWE-78"]
    category = VulnerabilityCategory.INJECTION
    description = "OS Command Injection via shell execution"
    default_severity = Severity.CRITICAL

    DANGEROUS_FUNCTIONS = {
        "python": {
            "os.system": "Shell command execution",
            "os.popen": "Shell command execution",
            "subprocess.call": "Subprocess execution",
            "subprocess.run": "Subprocess execution",
            "subprocess.Popen": "Subprocess execution",
            "subprocess.check_output": "Subprocess execution",
            "subprocess.check_call": "Subprocess execution",
            "commands.getoutput": "Shell command execution",
            "commands.getstatusoutput": "Shell command execution",
            "eval": "Code evaluation",
            "exec": "Code execution",
        },
        "javascript": {
            "eval": "Code evaluation",
            "exec": "Shell command execution",
            "execSync": "Shell command execution",
            "spawn": "Process spawn",
            "spawnSync": "Process spawn",
            "execFile": "File execution",
            "child_process.exec": "Shell command execution",
            "child_process.execSync": "Shell command execution",
        },
        "java": {
            "Runtime.exec": "Shell command execution",
            "Runtime.getRuntime().exec": "Shell command execution",
            "ProcessBuilder": "Process execution",
        },
        "php": {
            "exec": "Shell command execution",
            "shell_exec": "Shell command execution",
            "system": "Shell command execution",
            "passthru": "Shell command execution",
            "popen": "Shell command execution",
            "proc_open": "Process execution",
        },
    }

    # Patterns indicating variable/user input
    VARIABLE_INPUT_PATTERNS = [
        r"\([^)]*\+",  # function(... +
        r"\(f['\"]",   # function(f"...
        r"\([^)]*\{",  # function(...{
        r"\([^)]*\$",  # function(...$
        r"\([^)]*%",   # function(... %
        r"shell\s*=\s*True",  # shell=True
        r"`[^`]*\$\{",  # Backtick with ${...}
    ]

    # Backtick execution patterns (shell command in template literal)
    BACKTICK_PATTERNS = [
        (r"`[^`]*\$\{[^}]+\}[^`]*`", "backtick template with variable"),
    ]
