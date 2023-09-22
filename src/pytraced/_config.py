"""
_config.py:

This file contains all of the classes used for interacting with and constructing `Config` objects.

Classes:
    - `Config` - Class used for storing a logging configuration.
"""
from dataclasses import dataclass
from re import compile as compile_re
from typing import Callable, ClassVar

from ._record import Record


@dataclass(slots=True, frozen=True)
class Config:
    """
    Class used for storing a logging configuration.

    Class Variables:
        - `FORMAT_PARSER` - Compiled regular expression used for parsing log strings.
        - `DEFAUT` - Default format string for logging.

    Attributes:
        - `colourise` - Whether or not the colourise the output stream.
        - `min_level` - Minimum severity level which will be logged.
        - `filter_func` - Function used to determine whether or not a log should be written to the
                          stream. Returning false indicates that a log shouldn't be written.
        - `formatter` - Either a function which takes in a record and return the formatted string
                        ready for printing or a string which will be parsed and populated with
                        information at runtime.
    """

    FORMAT_PARSER: ClassVar = compile_re("%{.*?}%")
    DEFAULT: ClassVar = (
        "[%{lvl}%][%{time:YYYY-MM-DD hh:mm:ss.SSS z}%][%{trace:clean}%] - %{msg}%"
    )

    formatter: Callable[[Record], str] | str
    filter_func: Callable[[Record], bool] | None
    colourise: bool
    min_level: int
