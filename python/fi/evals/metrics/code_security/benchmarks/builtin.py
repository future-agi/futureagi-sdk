"""
Built-in benchmark test cases.

Curated test cases for common security evaluation scenarios.
"""

from .types import InstructTest, AutocompleteTest, RepairTest


# =============================================================================
# Python Instruct Mode Tests
# =============================================================================

from ._builtin_instruct import PYTHON_INSTRUCT_TESTS


# =============================================================================
# Python Autocomplete Mode Tests
# =============================================================================

from ._builtin_autocomplete import PYTHON_AUTOCOMPLETE_TESTS


# =============================================================================
# Python Repair Mode Tests
# =============================================================================

from ._builtin_repair import PYTHON_REPAIR_TESTS
