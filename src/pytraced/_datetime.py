"""
_datetime.py:

This file contains all of the functions required to format `datetime` objects for printing.

Functions:
    - `format_datetime` - Format the given datetime with the custom datetime specifiers.
"""
from calendar import day_abbr, day_name, month_abbr, month_name
from datetime import datetime, timedelta
from functools import lru_cache
from re import compile as compile_re
from typing import Callable, Mapping

from ._config import Config


def _add_timezone(date_time: datetime) -> datetime:
    """
    Add the current timezone to the `datetime` object.

    Parameters:
        - `date_time` - `datetime` object to add the local timezone to.

    Returns: `datetime` object with the local timezone.
    """
    return date_time.astimezone()


def _get_utc_offset(date_time: datetime) -> str | None:
    """Return the formatted UTC timezone offset if the `datetime` object has a timezone.

    Parameters:
        - `date_time` - `datetime` object.

    Returns: `None` if the `datetime` doesn't have `tzinfo` otherwise formatted utc offset.
    """

    offset = date_time.utcoffset()

    if not offset:
        return None

    sign = "+"

    if offset.days < 0:
        sign = "-"
        offset = -offset

    hours, remainder = divmod(offset, timedelta(hours=1))
    minutes, remainder = divmod(remainder, timedelta(minutes=1))
    seconds = remainder.seconds
    microseconds = offset.microseconds

    if microseconds:
        return f"{sign}{hours:02}{minutes:02}{seconds:02}.{microseconds:06}"

    if seconds:
        return f"{sign}{hours:02}{minutes:02}{seconds:02}"

    return f"{sign}{hours:02}{minutes:02}"


# Maps date format tokens to a function which returns the tokens value.
_DATE_TOKEN_MAP: Mapping[str, Callable[[datetime], str]] = {
    # fmt: off
    "YYYY": lambda d: str(d.year),                                 # full year
    "YY": lambda d: str(d.year % 100),                             # last two year digits

    "Q": lambda d: str((d.month // 4) + 1),                        # quarter

    "MMMM": lambda d: month_name[d.month],                         # month name
    "MMM": lambda d: month_abbr[d.month],                          # month abbreviation
    "MM": lambda d: f"{d.month:0>2}",                              # zero-padded month number
    "M": lambda d: str(d.month),                                   # month number

    "DDDD": lambda d: f"{d.timetuple().tm_yday:03}",               # zero-padded day of the year
    "DDD": lambda d: str(d.timetuple().tm_yday),                   # day of the year
    "DD": lambda d: f"{d.day:0>2}",                                # zero-padded day of the month
    "D": lambda d: str(d.day),                                     # day of the month

    "ddd": lambda d: day_name[d.day],                              # day name
    "dd": lambda d: day_abbr[d.day],                               # day abbreviation
    "d": lambda d: str(d.timetuple().tm_wday),                     # day of the week

    "A": lambda d: "AM" if d.hour < 12 else "PM",                  # am or pm

    "HH": lambda d: f"{((d.hour - 1) % 12) + 1:02}",               # zero-padded 12 hour
    "H": lambda d: str(((d.hour - 1) % 12) + 1),                   # 12 hour
    "hh": lambda d: f"{d.hour:0>2}",                               # zero-padded 24 hour
    "h": lambda d: str(d.hour),                                    # 24 hour

    "mm": lambda d: f"{d.minute:0>2}",                             # zero-padded minute
    "m": lambda d: str(d.minute),                                  # minute

    "ss": lambda d: f"{d.second:0>2}",                             # zero-padded second
    "s": lambda d: str(d.second),                                  # second

    "SSSSSS": lambda d: f"{d.microsecond:0>6}",                    # 6 digit zero-padded microsecond
    "SSSSS": lambda d: f"{d.microsecond // 10:0>5}",               # 5 digit zero-padded microsecond
    "SSSS": lambda d: f"{d.microsecond // 100:0>4}",               # 4 digit zero-padded microsecond
    "SSS": lambda d: f"{d.microsecond // 1_000:0>3}",              # 3 digit zero-padded microsecond
    "SS": lambda d: f"{d.microsecond // 10_000:0>2}",              # 2 digit zero-padded microsecond
    "S": lambda d: str(d.microsecond // 100_000),                  # 1 digit microsecond

    "Z": lambda d: _add_timezone(d).tzname() or "N/A",             # timezone name
    "z": lambda d: _get_utc_offset(_add_timezone(d)) or "N/A",     # utc offset

    "X": lambda d: str(d.timestamp()),                             # seconds timestamp
    "x": lambda d: str(int(d.timestamp() * 1e6) + d.microsecond),  # microseconds timestamp
}
_DATE_TOKEN_REGEXP = compile_re(f"({'|'.join(_DATE_TOKEN_MAP.keys())})+?")


def format_datetime(date_time: datetime, fmt: str) -> str:
    """
    Format a given `datetime` object using the custom token mapping.

    Parameters:
        - `date_time` - `datetime` object which represents the time to format.
        - `fmt` - Format to use with strftime.

    Returns: Formatted datetime.
    """
    return _DATE_TOKEN_REGEXP.sub(lambda m: _DATE_TOKEN_MAP[m.group()](date_time), fmt)


if Config.CACHE_FORMATTED_DATETIMES:
    format_datetime = lru_cache(maxsize=6)(format_datetime)
