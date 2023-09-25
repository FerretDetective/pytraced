"""
_config.py:

This file contains all of the classes used for interacting with and constructing `Config` objects.

Classes:
    - `Config` - Class used for storing a logging configuration.
"""
from dataclasses import dataclass
from re import compile as compile_re
from typing import Callable, ClassVar, final

from ._record import Record


@final
@dataclass(slots=True, frozen=True)
class Config:
    """
    Class used for storing global configuration for the `pytraced` package and a instance based
    logging configuration. To change the global configuration, one must directly modify the
    '.../pytraced/_config.py' file.

    Class Variables:
        - `FORMAT_PARSER` - Compiled regular expression used for parsing log strings.
        - `DEFAUT_FORMAT` - Default format string for logging.
        - `DEFAULT_TIME` - Default datetime format.
        - `DEFAULT_TRACE` - Default trace style.
        - `CACHE_FORMATTED_DATETIMES` - Controls the use an lru cache for previously formatted
                                        datetimes (maxsize=6). Defaults to true.
        - `CACHE_FORMATTED_PATHS` - Controls the use an unbounded cache for previously formatted
                                    paths to the files from which logs originate (maxsize=None).
                                    Defaults to true.

    Attributes:
        - `formatter` - Either a function which takes in a record and return the formatted string
                        ready for printing or a string which will be parsed and populated with
                        information at runtime.
        - `filter_func` - Function used to determine whether or not a log should be written to the
                          stream. Returning false indicates that a log shouldn't be written.
        - `colourise` - Whether or not the colourise the output stream.
        - `min_level` - Minimum severity level which will be logged.
    """

    FORMAT_PARSER: ClassVar = compile_re("%{.*?}%")
    DEFAULT_FORMAT: ClassVar = "[%{lvl}%][%{time}%][%{trace}%] - %{msg}%"
    DEFAULT_TIME: ClassVar = "YYYY-MM-DD hh:mm:ss.SSS z"
    DEFAULT_TRACE: ClassVar = "clean"
    CACHE_FORMATTED_DATETIMES: ClassVar = True
    CACHE_FORMATTED_PATHS: ClassVar = True

    formatter: Callable[[Record], str] | str
    filter_func: Callable[[Record], bool] | None
    colourise: bool
    min_level: int
