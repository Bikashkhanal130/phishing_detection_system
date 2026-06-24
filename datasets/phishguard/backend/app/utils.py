"""
utils.py
========
Small shared helpers.
"""

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


def as_aware_utc(dt: datetime) -> datetime:
    """
    Normalise a datetime to a timezone-aware UTC value.

    PostgreSQL TIMESTAMPTZ columns return aware datetimes, but some code paths
    (or SQLite in tests) may produce naive ones. This makes comparisons safe.
    """
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
