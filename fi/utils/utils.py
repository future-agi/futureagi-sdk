from fi.utils.constants import (
    MAX_FUTURE_YEARS_FROM_CURRENT_TIME,
    MAX_PAST_YEARS_FROM_CURRENT_TIME,
)


def is_timestamp_in_range(now: int, ts: int):
    max_time = now + (MAX_FUTURE_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60)
    min_time = now - (MAX_PAST_YEARS_FROM_CURRENT_TIME * 365 * 24 * 60 * 60)
    return min_time <= ts <= max_time
