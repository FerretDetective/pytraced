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
from traceback import format_exception, format_list
from typing import cast

from ._config import Config, FormatLiteral, TraceStyle
from ._record import Record
from .colours import add_colours


@lru_cache(maxsize=12)
def _format_date_time(date_time: datetime, fmt: str) -> str:
    """
    Format a given `datetime` object using strftime but replacing any occurence of '%f'
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
        - `record: Record` - Receord which contains all of the information to include in the log.
        - `config: Config` - Config which controls whether or not to add certain info to the log.

    Returns: `str` - String containing the info from the record according the to config.
    """
    last_end = 0
    logging_string = ""
    for match in Config.FORMAT_PARSER.finditer(format_str):
        logging_string += format_str[last_end : match.start()]
        last_end = match.end()
        cur_fmt = match.group()

        match cur_fmt:
            case FormatLiteral.NAME.value:
                logging_string += record.logger_name
            case FormatLiteral.LEVEL.value:
                logging_string += record.level.name
            case FormatLiteral.DATE_TIME.value:
                logging_string += _format_date_time(
                    record.date_time, cast(str, config.date_fmt)
                )
            case FormatLiteral.TRACE.value:
                match config.trace_style:
                    case TraceStyle.BARE:
                        logging_string += (
                            f"{basename(record.stack_trace[0].filename)}:"
                            f"{record.stack_trace[0].lineno}"
                        )
                    case TraceStyle.SIMPLE:
                        logging_string += (
                            f"{record.global_name}@{record.stack_trace[0].name}"
                            f":{record.stack_trace[0].lineno}"
                        )
                    case TraceStyle.CLEAN:
                        logging_string += (
                            f"{_format_path(record.stack_trace[0].filename)}@"
                            f"{record.stack_trace[0].name}:{record.stack_trace[0].lineno}"
                        )
                    case TraceStyle.DETAILED:
                        logging_string += " -> ".join(
                            (
                                f"{_format_path(trace.filename)}@{trace.name}:{trace.lineno}"
                                for trace in reversed(record.stack_trace)
                            )
                        )
                    case TraceStyle.FULL:
                        logging_string += "\n{}\n".format(
                            "\n".join(format_list(record.stack_trace[::-1]))
                        )
            case FormatLiteral.GLOBAL_NAME.value:
                logging_string += record.global_name
            case FormatLiteral.PROCESS_NAME.value:
                logging_string += record.process.name
            case FormatLiteral.PROCESS_ID.value:
                logging_string += str(record.process.ident)
            case FormatLiteral.THREAD_NAME.value:
                logging_string += record.thread.name
            case FormatLiteral.THREAD_ID.value:
                logging_string += str(record.thread.ident)
            case FormatLiteral.MESSAGE.value:
                if _from_msg:
                    logging_string += record.message
                else:
                    logging_string += _format(record.message, record, config, True)

    return logging_string + format_str[last_end:]


def format_record(record: Record, config: Config) -> str:
    """
    Create a logging string with the information from a record according to the config.

    Parameters:
        - `record: Record` - Record containing the information collected by the logger at runtime.
        - `config: Config` - Config which dictates where the info should be placed in the log.

    Returns: `str` - Formatted logging string ready for printing.
    """
    logging_string = _format(cast(str, config.formatter), record, config)

    if record.exception:
        # make sure the exception is on a newline unless the log is empty
        if logging_string:
            logging_string += "\n"
        logging_string += "".join(format_exception(record.exception))
    else:
        logging_string += "\n"

    if config.colourize and record.level.colours is not None:
        return add_colours(logging_string, *record.level.colours)

    return logging_string
