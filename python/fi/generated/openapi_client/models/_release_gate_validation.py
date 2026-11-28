"""Generated validation for closed release-gate inputs."""

from typing import Any

from jsonschema import Draft7Validator, FormatChecker, validators

SCHEMAS = {
    "ReleaseGateCase": {
        "additionalProperties": False,
        "properties": {
            "example_id": {"format": "uuid", "title": "Example id", "type": "string"},
            "trial_number": {
                "maximum": 2147483647,
                "minimum": 1,
                "title": "Trial number",
                "type": "integer",
            },
        },
        "required": ["example_id", "trial_number"],
        "type": "object",
    },
    "ReleaseGatePolicy": {
        "additionalProperties": False,
        "properties": {
            "critical_cases": {
                "default": [],
                "items": {"$ref": "#/components/schemas/ReleaseGateCase"},
                "maxItems": 10000,
                "type": "array",
            },
            "max_regressions": {
                "default": 0,
                "minimum": 0,
                "title": "Max regressions",
                "type": "integer",
            },
        },
        "type": "object",
    },
}

_StrictValidator = validators.extend(
    Draft7Validator,
    type_checker=Draft7Validator.TYPE_CHECKER.redefine(
        "integer", lambda _checker, value: type(value) is int
    ),
)
_validators = {
    name: _StrictValidator(
        {"$ref": "#/components/schemas/" + name, "components": {"schemas": SCHEMAS}},
        format_checker=FormatChecker(),
    )
    for name in SCHEMAS
}


def validate_release_gate(value: Any, schema_name: str) -> None:
    _validators[schema_name].validate(value)
