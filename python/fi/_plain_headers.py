"""Exporter headers copied once into a plain ``dict`` of plain ``str``/``bytes`` names and values.

The key checks read a header with ``str(value)``, while ``requests``/``http.client`` and gRPC send ``value.encode()``
or the ``str`` content. A ``str`` or ``bytes`` subclass can give other text to each of those reads, so each name and
value is read once, as its stored content, and that plain copy is the one both the checks and the wire receive.
"""

from typing import Any, Optional


def plain_header_value(value: Any) -> Any:
    """``value`` as a plain ``str`` or ``bytes`` holding its stored content; ``None`` stays ``None``. Any other object
    is read once with ``str()``."""
    if value is None or type(value) in (str, bytes):
        return value
    if isinstance(value, str):
        return str.__str__(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(memoryview(value))
    return str(value)


def plain_header_copy(given: Any) -> Optional[dict]:
    """A plain ``dict`` copy of ``given`` with plain names and values, or ``None`` when ``given`` is a plain ``dict``
    whose names and values are all plain ``str``/``bytes`` (or ``None`` values) and can be handed on as it is.

    A ``dict`` subclass is read as a ``requests`` session reads it (each name, then its value by name); any other
    header form is read through ``header_pairs`` once, so an iterator of pairs is kept."""
    if given is None:
        return None
    if type(given) is dict:
        if all(type(name) in (str, bytes) and (value is None or type(value) in (str, bytes))
               for name, value in dict.items(given)):
            return None
        pairs = list(dict.items(given))
    elif isinstance(given, dict):
        pairs = [(name, given[name]) for name in given]
    else:
        from fi._core.proxy_routing import header_pairs

        pairs = header_pairs(given)
    return {plain_header_value(name): plain_header_value(value) for name, value in pairs}
