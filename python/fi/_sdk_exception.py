"""The SDK's base exception, in a module that imports nothing from ``fi.utils``.

``fi.utils.errors`` re-exports :class:`SDKException` from here, so existing imports keep
working, while ``fi.experiments.errors`` and ``fi._credentials`` can subclass it without
importing ``fi.utils`` (another distribution also ships ``fi/utils``).
"""

from typing import Optional


class SDKException(Exception):
    """Base exception for all SDK errors."""

    def __init__(self, message: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        self.custom_message = message  # Store custom message if provided
        # annotated as BaseException's own attribute, so type checkers see no ambiguous override
        self.__cause__: Optional[BaseException] = cause
        super().__init__(message or self.get_message())  # Use get_message if no specific message is passed

    def __str__(self) -> str:
        """Default string representation for all exceptions."""
        # If a specific message was passed to constructor, use it. Otherwise, use get_message().
        return self.custom_message or self.get_message()

    def get_message(self) -> str:
        """Return a human-readable error message. Subclasses should override this."""
        if self.__cause__:
            return f"An SDK error occurred, caused by: {self.__cause__}"
        return "An unknown error occurred in the SDK."

    def get_error_code(self) -> str:
        """Return a machine-readable error code. Subclasses should override this."""
        return "UNKNOWN_SDK_ERROR"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.get_message()}', code='{self.get_error_code()}')"
