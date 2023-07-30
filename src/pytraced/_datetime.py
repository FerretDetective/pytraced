"""
_datetime.py:

This file contains the function used by the `Logger` to get the current date & time.

Function:
    - `get_datetime` - Get the current date & time in a timezone aware `datetime` object.
"""
from datetime import datetime, tzinfo

# cache the current timezone to avoid having to recompute it
_tz: tzinfo = datetime.now().astimezone().tzinfo  # type: ignore


def get_datetime() -> datetime:
    """
    Get the current date & time in a timezone aware `datetime` object
    using the cached current timezone.

    Returns: `datetime` - Current date & time as a timezone aware `datetime`.
    """
    return datetime.now(_tz)
