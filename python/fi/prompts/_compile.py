"""Pure prompt rendering; never sends a request or mutates the stored template."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping, Sequence
from typing import Any

_VARIABLE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def compile_prompt(
    template: Mapping[str, Any], variables: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Render text and message placeholders; keep missing variables unresolved.

    Accept a retrieved wire template (``prompt_config``), or a mapping with
    ``messages``. Multimodal parts and tool-call metadata retain their shape.
    """
    values = variables or {}
    source = template.get("result", template)
    if not isinstance(source, Mapping):
        raise ValueError("template must contain a message mapping")
    config = source.get("prompt_config", source)
    if isinstance(config, list):
        config = config[0] if config else {}
    if not isinstance(config, Mapping):
        raise ValueError("prompt_config must contain a message mapping")
    messages = config.get("messages")
    if not isinstance(messages, list):
        raise ValueError("template must contain a messages list")

    def render(value: Any) -> Any:
        if isinstance(value, str):
            return _VARIABLE.sub(
                lambda match: str(values[match[1]]) if match[1] in values else match[0], value,
            )
        if isinstance(value, list):
            return [render(item) for item in value]
        if isinstance(value, Mapping):
            return {key: render(item) for key, item in value.items()}
        return copy.deepcopy(value)

    def message(value: Any) -> dict[str, Any]:
        if not isinstance(value, Mapping) or "role" not in value or "content" not in value:
            raise ValueError("each chat message must include role and content")
        result = copy.deepcopy(dict(value))
        result["content"] = render(value["content"])
        return result

    compiled: list[dict[str, Any]] = []
    for item in messages:
        if isinstance(item, Mapping) and item.get("type") == "placeholder":
            name = item.get("name")
            if name not in values:
                compiled.append(copy.deepcopy(dict(item)))
                continue
            replacement = values[name]
            if not isinstance(replacement, Sequence) or isinstance(replacement, (str, bytes)):
                raise ValueError("message placeholders must be lists of chat messages")
            compiled.extend(message(entry) for entry in replacement)
        else:
            compiled.append(message(item))
    return compiled
