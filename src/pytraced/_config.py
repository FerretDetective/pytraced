"""
_config.py:

This file contains all of the classes used for interacting with and constructing `Config` objects.

Enums:
    - `TraceStyle` - Enum used to keep track of stack styles for the `Config` object.
    - `FormatLiteral` - Enum containing the format specifiers for which represents info gathered at
                        runtime.

Classes:
    - `InvalidFormatSpecifierError` - Error raised when the parser encounters a format specifier
                                      which does not exist.
    - `Config` - Class used for storing a logging configuration.
"""
from enum import Enum, auto
from re import compile as compile_re
from typing import Callable

from ._record import Record


class TraceStyle(Enum):
    """
    This enum is used to keep track of which style of stack trace the used specified in the config.

    Options:
        - `BARE` - Bare-bones stack trace including only the filename and lineno. (main.py:5)
        - `SIMPLE` - Simple stack trace including the global `__name__`, the enclosing function,
                     and the lineno. (__main__@main:5)
        - `CLEAN` - Simple yet informative trace including relative path to the file, the enclosing
                    function, & the lineno. (src/main.py@main:5)
        - `DETAILED` - Detailed stack trace including the info provided by the CLEAN info for entire
                       traceback. (src/main.py@<module>:9 -> src/main.py@main:5)
        - `FULL` - The full unprocessed python traceback.
    """

    BARE = auto()
    SIMPLE = auto()
    CLEAN = auto()
    DETAILED = auto()
    FULL = auto()


class FormatLiteral(Enum):
    """
    This enum contains the format specifiers for all of the possible
    pieces of information the logger can print.

    Options:
        - `NAME = "%{name}%"` - Name of the logger which the record was produced by.
        - `GLOBAL_NAME = "%{gname}%"` - Global `__name__` from where the log was produced.
        - `LEVEL = "%{lvl}%"` - Level/severity of the log.
        - `DATE_TIME = "%{date_time}%"` - Time & data of when the log was produced.
        - `TRACE = "%{trace}%"` - Stack trace of the currently executing frame where the log was
                                  produced.
        - `MESSAGE = "%{msg}%"` - Additional information which was added to the record.
        - `PROCESS_NAME = "%{pname}%"` - Name of the currently executing process from where the
                                         log was produced.
        - `PROCESS_ID = "%{pid}%"` - Id of the currently executing process from where the log was
                                     produced.
        - `THREAD_NAME = "%{tname}%"` - Name of the currently executing thread from where the log
                                        was produced.
        - `THREAD_ID = "%{tid}%"` - Id of the currently executing thread from where the log was
                                    produced.
    """

    NAME = "%{name}%"
    GLOBAL_NAME = "%{gname}%"
    LEVEL = "%{lvl}%"
    DATE_TIME = "%{date_time}%"
    TRACE = "%{trace}%"
    MESSAGE = "%{msg}%"
    PROCESS_NAME = "%{pname}%"
    PROCESS_ID = "%{pid}%"
    THREAD_NAME = "%{tname}%"
    THREAD_ID = "%{tid}%"


class InvalidFormatSpecifierError(Exception):
    """
    This class should be used to raise an error when the parser
    encounters a format specifier which does not exist.
    """


class Config:
    """
    Class used for storing a logging configuration.

    Class Variables:
        - `FORMAT_PARSER: Pattern[str]` - Compiled regular expression used for parsing log strings.
        - `DEFAULT: str` - Default format string for logging.

    Attributes:
        - `colourise: bool` - Whether or not the colourise the output stream.
        - `min_level: int` - Minimum severity level which will be logged.
        - `filter_func: Callable[[Record], bool]
                        | None = None` - Function used to determine whether or not a log should
                                         be written to the stream. Returning false indicates that
                                         a log shouldn't be written.
        - `date_fmt: str | None = None` - Datetime format string which will be passed to strftime.
        - `trace_style: StackTraceStyle | None = NOne` - Style to stack trace to use for formatting.
        - `formatter: Callable[[Record], str]
                      | str` - Either a function which takes in a record and return the formatted
                               string ready for printing or a string which will be parsed and
                               populated with information at runtime.
    """

    __slots__ = (
        "formatter",
        "date_fmt",
        "trace_style",
        "colourise",
        "min_level",
        "filter_func",
    )

    FORMAT_PARSER = compile_re("%{.*?}%")
    DEFAULT = (
        "[%{lvl}%][%{time:yyyy-mm-dd HH:MM:SS.FS tzo}%][%{trace:clean}%] - %{msg}%"
    )

    def __init__(
        self,
        log_format: Callable[[Record], str] | str,
        filter_func: Callable[[Record], bool] | None,
        colourise: bool,
        min_level: int,
    ) -> None:
        self.colourise = colourise
        self.min_level = min_level
        self.filter_func = filter_func
        self.date_fmt: str | None = None
        self.trace_style: TraceStyle | None = None
        self.formatter = log_format

        if callable(log_format):
            return

        last_end = 0
        format_string = ""
        for match in Config.FORMAT_PARSER.finditer(log_format):
            format_string += log_format[last_end : match.start()]
            last_end = match.end()
            cur_fmt = match.group()

            if cur_fmt == "%{name}%":
                format_string += FormatLiteral.NAME.value
            elif cur_fmt in ("%{lvl}%", "%{level}%"):
                format_string += FormatLiteral.LEVEL.value
            elif cur_fmt == "%{time}%" or (
                cur_fmt.startswith("%{time:") and cur_fmt[-2:] == "}%"
            ):
                if ":" in cur_fmt:
                    self.date_fmt = (
                        cur_fmt[cur_fmt.index(":") + 1 : -2]  # ignore ':' & '}%'
                        .replace("yyyy", "%Y")
                        .replace("yy", "%y")
                        .replace("mm", "%m")
                        .replace("dd", "%d")
                        .replace("HH", "%H")
                        .replace("MM", "%M")
                        .replace("SS", "%S")
                        .replace("FS", "%f")
                        .replace("tzo", "%z")
                        .replace("tzn", "%Z")
                    )
                else:
                    self.date_fmt = "%Y-%m-%d %H:%M:%S.%f %z"

                format_string += FormatLiteral.DATE_TIME.value
            elif (
                cur_fmt == "%{trace}%"
                or cur_fmt.startswith("%{trace:")
                and cur_fmt[-2:] == "}%"
            ):
                if ":" in cur_fmt:
                    style = cur_fmt[cur_fmt.index(":") + 1 : -2]  # ignore ':' & '}%'
                    try:
                        self.trace_style = TraceStyle[style.upper()]
                    except KeyError:
                        raise InvalidFormatSpecifierError(  # pylint: disable=raise-missing-from
                            f"the format specifier: {style!r} is invalid"
                        )
                else:
                    self.trace_style = TraceStyle.CLEAN

                format_string += FormatLiteral.TRACE.value
            elif cur_fmt in ("%{gname}%", "%{global-name}%"):
                format_string += FormatLiteral.GLOBAL_NAME.value
            elif cur_fmt in ("%{pname}%", "%{process-name}%"):
                format_string += FormatLiteral.PROCESS_NAME.value
            elif cur_fmt in ("%{pid}%", "%{process-id}%"):
                format_string += FormatLiteral.PROCESS_ID.value
            elif cur_fmt in ("%{tname}%", "%{thread-name}%"):
                format_string += FormatLiteral.THREAD_NAME.value
            elif cur_fmt in ("%{tid}%", "%{thread-id}%"):
                format_string += FormatLiteral.THREAD_ID.value
            elif cur_fmt in ("%{msg}%", "%{message}%"):
                format_string += FormatLiteral.MESSAGE.value
            else:
                raise InvalidFormatSpecifierError(
                    f"format specifier {cur_fmt!r} is invalid"
                )
        self.formatter = format_string + log_format[last_end:]

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(colourise={self.colourise}, min_level={self.min_level}, "
            f"log_format={self.formatter}, filter_func={self.filter_func})"
        )

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}{{ formatter: {self.formatter!r}, "
            f"date_fmt: {self.date_fmt!r}, trace_style: {self.trace_style!r}, "
            f"colourise: {self.colourise}, min_level: {self.min_level}, "
            f"filter_func: {self.filter_func!r}}}"
        )
