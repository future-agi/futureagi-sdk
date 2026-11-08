"""Support for classes whose methods live in ``_*Methods`` bases in other modules.

A moved method's annotations can name its own class (``-> "StreamingEvaluator"``), and
``typing.get_type_hints`` resolves them in the globals of the module that defines the method. That
module cannot import the class at run time (the class's module imports it first), so it declares the
class under ``TYPE_CHECKING`` for static tools, and the class's module binds the class there, right
after the class statement, for run-time tools.
"""

import sys


def bind_owner(cls: type) -> type:
    """Bind ``cls`` by name in the module of each of its ``_*Methods`` bases; returns ``cls``."""
    for base in cls.__bases__:
        if base.__name__.startswith("_") and base.__name__.endswith("Methods"):
            vars(sys.modules[base.__module__]).setdefault(cls.__name__, cls)
    return cls
