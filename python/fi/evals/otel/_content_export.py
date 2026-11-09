"""Apply configured prompt/completion privacy at the exporter boundary."""

from contextvars import ContextVar
from copy import copy
from functools import wraps
import logging
import re

from .config import ContentConfig


logger = logging.getLogger(__name__)

_PROMPT_KEYS = frozenset({
    "gen_ai.input.messages", "gen_ai.system_instructions",
    "llm.prompt", "prompt", "input", "llm.messages", "messages",
})
_COMPLETION_KEYS = frozenset({
    "gen_ai.output.messages", "llm.completion", "completion", "output",
    "response", "llm.choices", "choices",
})


class _ContentPolicy:
    def __init__(self, config):
        # Snapshot settings: providers retain their own policy after setup returns.
        self.capture_prompts = config.capture_prompts
        self.capture_completions = config.capture_completions
        self.max_length = config.max_content_length
        self.patterns = []
        for pattern in config.redact_patterns:
            try:
                self.patterns.append(re.compile(pattern))
            except re.error:
                logger.warning("Invalid content redaction pattern ignored")

    def _content(self, value):
        if isinstance(value, str):
            # Redact first so a length limit cannot leave a partial match exposed.
            for pattern in self.patterns:
                value = pattern.sub("[REDACTED]", value)
            if len(value) > self.max_length:
                value = value[:self.max_length] + "... [truncated]"
        elif isinstance(value, (tuple, list)):
            value = tuple(self._content(item) for item in value)
        return value

    def span(self, span):
        from opentelemetry.attributes import BoundedAttributes

        attributes = dict(span.attributes or {})
        changed = False
        for key, value in tuple(attributes.items()):
            if key in _PROMPT_KEYS or re.fullmatch(r"gen_ai\.prompt\.\d+\.content", key):
                capture = self.capture_prompts
            elif key in _COMPLETION_KEYS or re.fullmatch(r"gen_ai\.completion\.\d+\.content", key):
                capture = self.capture_completions
            else:
                continue
            if not capture:
                del attributes[key]
                changed = True
            else:
                sanitized = self._content(value)
                if sanitized != value:
                    attributes[key] = sanitized
                    changed = True
        if not changed:
            return span

        # ReadableSpan has no attribute setter. Copy its view, not the live span:
        # console to_json() and OTLP encoders must both see the same safe mapping.
        result = copy(span)
        result._attributes = BoundedAttributes(attributes=attributes, immutable=True)
        result._attributes.dropped = span.dropped_attributes
        return result


class _ContentExporter:
    def __init__(self, exporter, policy):
        self._exporter = exporter
        self._policy = policy

    def export(self, spans):
        return self._exporter.export(tuple(self._policy.span(span) for span in spans))

    def shutdown(self):
        return self._exporter.shutdown()

    def force_flush(self, timeout_millis=30000):
        return self._exporter.force_flush(timeout_millis=timeout_millis)


def _configure_content_exports(namespace):
    """Adapt setup and its factory without changing their legacy implementations."""
    setup = namespace["setup_tracing"]
    create_exporter = namespace["_create_exporter"]
    policy_context = ContextVar("tracing_content_policy", default=None)

    @wraps(setup)
    def setup_with_content(*args, **kwargs):
        config = args[0] if args else kwargs.get("config")
        content = config.content if config is not None else kwargs.get("content", ContentConfig())
        # Default settings must not add export-time truncation to manual spans.
        policy = None if content == ContentConfig() else _ContentPolicy(content)
        token = policy_context.set(policy)
        try:
            return setup(*args, **kwargs)
        finally:
            policy_context.reset(token)

    @wraps(create_exporter)
    def create_content_exporter(*args, **kwargs):
        exporter = create_exporter(*args, **kwargs)
        policy = policy_context.get()
        if exporter is not None and policy is not None:
            return _ContentExporter(exporter, policy)
        return exporter

    namespace["setup_tracing"] = setup_with_content
    namespace["_create_exporter"] = create_content_exporter
