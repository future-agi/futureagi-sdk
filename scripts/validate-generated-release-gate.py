"""Add strict validation to the generated release-gate input models.

The Python generator intentionally preserves unknown keys only for schemas that
allow additional properties.  The release-gate policy and case schemas are
closed, so silently dropping a misspelled policy would change the caller's
request before it reaches the API.  This post-hook copies the reviewed schema
from the generated OpenAPI document and wraps only those two generated models.
It is rerunnable and contains no hand-maintained field list.
"""

from __future__ import annotations

import json
from pprint import pformat
import sys
from pathlib import Path


def main() -> None:
    spec_path, models_dir = map(Path, sys.argv[1:])
    spec = json.loads(spec_path.read_text())
    schemas = spec["components"]["schemas"]
    if "ReleaseGatePolicy" not in schemas:
        return
    selected = {
        name: schemas[name] for name in ("ReleaseGatePolicy", "ReleaseGateCase")
    }
    helper = models_dir / "_release_gate_validation.py"
    helper.write_text(
        '"""Generated validation for closed release-gate inputs."""\n'
        "from typing import Any\n\n"
        "from jsonschema import Draft7Validator, FormatChecker, validators\n\n"
        f"SCHEMAS = {pformat(selected, width=88, sort_dicts=True)}\n\n"
        "_StrictValidator = validators.extend(\n"
        "    Draft7Validator, type_checker=Draft7Validator.TYPE_CHECKER.redefine(\n"
        '        "integer", lambda _checker, value: type(value) is int\n'
        "    )\n)\n"
        "_validators = {\n"
        '    name: _StrictValidator({"$ref": "#/components/schemas/" + name,\n'
        '        "components": {"schemas": SCHEMAS}}, format_checker=FormatChecker())\n'
        "    for name in SCHEMAS\n}\n\n"
        "def validate_release_gate(value: Any, schema_name: str) -> None:\n"
        "    _validators[schema_name].validate(value)\n"
    )

    wrappers = {
        "release_gate_policy.py": "policy",
        "release_gate_case.py": "case",
    }
    for filename, kind in wrappers.items():
        path = models_dir / filename
        text = path.read_text()
        function = "validate_release_gate"
        schema_name = "ReleaseGate" + kind.title()
        import_line = f"from ._release_gate_validation import {function}\n"
        if import_line not in text:
            marker = "from attrs import define as _attrs_define\n"
            if text.count(marker) != 1:
                raise ValueError(f"Generated model changed: {path}")
            text = text.replace(marker, marker + "\n" + import_line, 1)
        source_marker = "        d = dict(src_dict)\n"
        if text.count(source_marker) != 1:
            raise ValueError(f"Generated parser changed: {path}")
        if f'        {function}(src_dict, "{schema_name}")\n' not in text:
            text = text.replace(
                source_marker,
                f'        {function}(src_dict, "{schema_name}")\n\n' + source_marker,
                1,
            )
        return_marker = "        return field_dict\n"
        if text.count(return_marker) != 1:
            raise ValueError(f"Generated serializer changed: {path}")
        if f'        {function}(field_dict, "{schema_name}")\n' not in text:
            text = text.replace(
                return_marker,
                f'        {function}(field_dict, "{schema_name}")\n\n' + return_marker,
                1,
            )
        path.write_text(text)


if __name__ == "__main__":
    main()
