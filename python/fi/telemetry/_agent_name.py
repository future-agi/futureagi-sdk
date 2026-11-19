"""Track the writer, not name equality. Only observe spans we actually stamp."""
from __future__ import annotations

NAME = 'gen_ai.agent.name'


class _Origin:
    automatic = False


def automatic(span):
    origin = getattr(getattr(span, 'set_attribute', None), '_fi_agent_origin', None)
    return type(origin) is _Origin and origin.automatic


def write_context_name(span, name):
    setter = span.set_attribute
    setter(NAME, name)
    origin = getattr(setter, '_fi_agent_origin', None)
    if type(origin) is not _Origin:
        # Even a later write of the *same* string is a framework override. OTel
        # has no attribute change listener. Observe its two public writer APIs
        # on this span only; no global patches, span retention or export keys.
        origin = _Origin()
        def set_attribute(key, value):
            if key == NAME:
                origin.automatic = False
            return setter(key, value)
        set_attribute._fi_agent_origin = origin
        try:
            bulk = span.set_attributes
            def set_attributes(attributes):
                if NAME in attributes:
                    origin.automatic = False
                return bulk(attributes)
            span.set_attributes = set_attributes
            span.set_attribute = set_attribute
        except (AttributeError, TypeError):
            # Non-standard/read-only span: do not claim an unobservable write.
            return
    origin.automatic = True
