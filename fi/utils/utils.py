import os
import tempfile

from fi.utils.constants import (
    MAX_FUTURE_YEARS_FROM_CURRENT_TIME,
    MAX_PAST_YEARS_FROM_CURRENT_TIME,
)


def is_timestamp_in_range(now: int, ts: int):
    max_time = now + (MAX_FUTURE_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60)
    min_time = now - (MAX_PAST_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60)
    return min_time <= ts <= max_time


def get_tempfile_path(prefix: str, suffix: str) -> str:
    """Create a temporary file with a random name and given suffix.

    Args:
        prefix (str): Prefix to prepend to the random filename.
        suffix (str): Suffix to append to the random filename.

    Returns:
        str: Path to the created temporary file.
    """
    # Create temporary file with given prefix and suffix
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)  # Close the file descriptor
    return path
