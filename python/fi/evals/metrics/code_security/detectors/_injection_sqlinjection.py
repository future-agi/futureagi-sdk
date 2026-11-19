"""Sqlinjection for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    BaseDetector, Severity, VulnerabilityCategory, _SQLInjectionDetectorDetectMethods,
    register_detector,
)

@register_detector("sql_injection")
class SQLInjectionDetector(_SQLInjectionDetectorDetectMethods, BaseDetector):
    """
    Detects SQL injection vulnerabilities (CWE-89).

    Identifies:
    - String concatenation in SQL queries
    - f-string/format string in SQL
    - Raw string interpolation
    - Missing parameterized queries

    Examples of vulnerable code:
        query = "SELECT * FROM users WHERE id = " + user_id
        query = f"SELECT * FROM users WHERE name = '{name}'"
        cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
    """

    name = "sql_injection"
    cwe_ids = ["CWE-89"]
    category = VulnerabilityCategory.INJECTION
    description = "SQL Injection via string concatenation or interpolation"
    default_severity = Severity.HIGH

    # SQL keywords to look for
    SQL_KEYWORDS = [
        "select", "insert", "update", "delete", "drop", "create",
        "alter", "exec", "execute", "union", "truncate", "grant",
    ]

    # Patterns indicating unsafe SQL construction
    UNSAFE_PATTERNS = {
        "python": [
            # f-string with SQL
            (r'f["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*\{', "f-string SQL interpolation"),
            # String concatenation
            (r'["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*["\']\s*\+', "String concatenation in SQL"),
            (r'\+\s*["\'].*(?:' + "|".join(SQL_KEYWORDS) + r')', "String concatenation in SQL"),
            # % formatting
            (r'["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*%s.*["\']\s*%', "%-format SQL interpolation"),
            # .format()
            (r'["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*\{\}.*["\']\.format\(', ".format() SQL interpolation"),
        ],
        "javascript": [
            # Template literal
            (r'`.*(?:' + "|".join(SQL_KEYWORDS) + r').*\$\{', "Template literal SQL interpolation"),
            # String concatenation
            (r'["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*["\']\s*\+', "String concatenation in SQL"),
        ],
        "java": [
            # String concatenation
            (r'".*(?:' + "|".join(SQL_KEYWORDS) + r').*"\s*\+', "String concatenation in SQL"),
            # String.format
            (r'String\.format\s*\(\s*".*(?:' + "|".join(SQL_KEYWORDS) + r')', "String.format SQL"),
        ],
        "php": [
            # Variable interpolation
            (r'".*(?:' + "|".join(SQL_KEYWORDS) + r').*\$', "Variable interpolation in SQL"),
            # String concatenation
            (r'["\'].*(?:' + "|".join(SQL_KEYWORDS) + r').*["\']\s*\.', "String concatenation in SQL"),
        ],
    }

    # Safe patterns (parameterized queries)
    SAFE_PATTERNS = {
        "python": [
            r"execute\s*\([^,]+,\s*[\[\(]",  # execute(query, (params,))
            r"executemany\s*\([^,]+,",  # executemany(query, params)
            r"\.filter\s*\(",  # ORM filter
            r"\.where\s*\(",  # ORM where
        ],
        "javascript": [
            r"\?\s*,",  # Prepared statement placeholder
            r"query\s*\([^,]+,\s*\[",  # query(sql, [params])
        ],
        "java": [
            r"prepareStatement",  # Prepared statement
            r"setString\s*\(",  # Parameter binding
            r"setInt\s*\(",
        ],
    }
