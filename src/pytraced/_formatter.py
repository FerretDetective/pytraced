"""
_formatter.py:

This file contains all of the functions required to format `Record`s according to `Config`s.

Functions:
    - `format_record` - Get a string with the info from a record according to the config.
"""
from datetime import datetime
from functools import lru_cache
from os.path import basename
from pathlib import Path
from traceback import extract_stack, format_exception, format_stack

from ._config import Config, FormatLiteral, InvalidFormatSpecifierError, TraceStyle
from ._record import Record
from .colours import add_colours


@lru_cache(maxsize=12)
def _format_date_time(date_time: datetime, fmt: str) -> str:
    """
    Format a given `datetime` object using strftime but replacing any occurrence of '%f'
    with the microseconds to 3 digits.

    Parameters:
        - `date_time: datetime` - `datetime` object which represents the time to format.
        - `fmt: str` - Format to use with strftime.

    Returns: `str` - Formatted datetime.
    """
    return date_time.strftime(fmt.replace("%f", f"{date_time.microsecond:0>6}"[:-3]))


@lru_cache(maxsize=None)  # unbounded cache for the lifetime of the program
def _format_path(str_path: str) -> str:
    """
    If possible return the path formatted to be relative to the cwd.

    Parameters:
        - `str_path: str` - String path to format.

    Returns: `str` - Formatted path.
    """

    try:
        return str(Path(str_path).relative_to(Path.cwd()))
    except ValueError:
        return str_path


def _format(
    format_str: str, record: Record, config: Config, _from_msg: bool = False
) -> str:
    """
    Format a the format string with the information from the record according the to config.

    Parameters:
        - `format_str: str` - Format string which dictates where the info from the record should go.
        - `record: Record` - Record which contains all of the information to include in the log.
        - `config: Config` - Config which controls whether or not to add certain info to the log.

    Returns: `str` - String containing the info from the record according the to config.

    Raises:
        - `InvalidFormatSpecifierError` - Raised if a format specifier cannot be matched to
                                          `extra_info` or default types.
    """
    last_end = 0
    logging_string = ""
    for match in Config.FORMAT_PARSER.finditer(format_str):
        logging_string += format_str[last_end : match.start()]
        last_end = match.end()
        cur_fmt = match.group()

        if cur_fmt == FormatLiteral.NAME.value:
            logging_string += record.logger_name
        elif cur_fmt == FormatLiteral.LEVEL.value:
            logging_string += record.level.name
        elif cur_fmt == FormatLiteral.DATE_TIME.value:
            logging_string += _format_date_time(record.date_time, config.date_fmt)
        elif cur_fmt == FormatLiteral.TRACE.value:
            match config.trace_style:
                case TraceStyle.BARE:
                    logging_string += (
                        f"{basename(record.frame.f_code.co_filename)}:"
                        f"{record.frame.f_lineno}"
                    )
                case TraceStyle.SIMPLE:
                    logging_string += (
                        f"{record.global_name}@{record.frame.f_code.co_name}"
                        f":{record.frame.f_lineno}"
                    )
                case TraceStyle.CLEAN:
                    logging_string += (
                        f"{_format_path(record.frame.f_code.co_filename)}@"
                        f"{record.frame.f_code.co_name}:{record.frame.f_lineno}"
                    )
                case TraceStyle.DETAILED:
                    logging_string += " -> ".join(
                        (
                            f"{_format_path(trace.filename)}@{trace.name}:{trace.lineno}"
                            for trace in extract_stack(record.frame)
                        )
                    )
                case TraceStyle.FULL:
                    logging_string += "\n{}\n".format(
                        "\n".join(format_stack(record.frame))
                    )
        elif cur_fmt == FormatLiteral.GLOBAL_NAME.value:
            logging_string += record.global_name
        elif cur_fmt == FormatLiteral.PROCESS_NAME.value:
            logging_string += record.process.name
        elif cur_fmt == FormatLiteral.PROCESS_ID.value:
            logging_string += str(record.process.ident)
        elif cur_fmt == FormatLiteral.THREAD_NAME.value:
            logging_string += record.thread.name
        elif cur_fmt == FormatLiteral.THREAD_ID.value:
            logging_string += str(record.thread.ident)
        elif cur_fmt == FormatLiteral.MESSAGE.value:
            if _from_msg:
                logging_string += record.message
            else:
                logging_string += _format(record.message, record, config, True)
        else:
            if not record.extra_info:
                raise InvalidFormatSpecifierError(
                    f"Format specifier {cur_fmt!r} does not exist"
                )

            missing = object()
            info = record.extra_info.get(cur_fmt, missing)
            if info is missing:
                raise InvalidFormatSpecifierError(
                    f"Format specifier {cur_fmt!r} does not exist"
                )

            logging_string += str(info)

    return logging_string + format_str[last_end:]


def format_record(record: Record, config: Config) -> str:
    """
    Create a logging string with the information from a record according to the config.

    Parameters:
        - `record: Record` - Record containing the information collected by the logger at runtime.
        - `config: Config` - Config which dictates where the info should be placed in the log.

    Returns: `str` - Formatted logging string ready for printing.
    """
    logging_string = _format(config.formatter, record, config)  # type: ignore

    if record.exception is not None:
        # make sure the exception is on a newline unless the log is empty
        if logging_string:
            logging_string += "\n"
        logging_string += "".join(format_exception(record.exception))
    else:
        logging_string += "\n"

    if config.colourise and record.level.colours is not None:
        return add_colours(logging_string, *record.level.colours)

    return logging_string
