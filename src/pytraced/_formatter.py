"""
_formatter.py:

This file contains all of the functions required to format `Record`s according to `Config`s.

Functions:
    - `format_record` - Get a string with the info from a record according to the config.
"""
from functools import lru_cache
from os.path import basename
from pathlib import Path
from traceback import extract_stack, format_exception, format_stack

from ._config import Config
from ._datetime import format_datetime
from ._record import Record
from .colours import add_colours


class InvalidFormatSpecifierError(Exception):
    """
    This class should be used to raise an error when the parser
    encounters a format specifier which does not exist.
    """


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


def _format(format_str: str, record: Record, *, _from_msg: bool = False) -> str:
    """
    Format a the format string with the information from the record according the to config.

    Parameters:
        - `format_str: str` - Format string which dictates where the info from the record should go.
        - `record: Record` - Record which contains all of the information to include in the log.

    Returns: `str` - String containing the info from the record according the to config.

    Raises:
        - `InvalidFormatSpecifierError` - Raised if parser encounters an invalid format specifier.
    """
    last_end = 0
    logging_string = ""
    for match in Config.FORMAT_PARSER.finditer(format_str):
        logging_string += format_str[last_end : match.start()]
        last_end = match.end()
        cur_fmt = match.group()

        if cur_fmt == "%{name}%":
            logging_string += record.logger_name
        elif cur_fmt in ("%{lvl}%", "%{level}%"):
            logging_string += record.level.name
        elif cur_fmt.startswith("%{time"):
            logging_string += format_datetime(
                record.date_time,
                "YYYY-MM-DD hh:mm:ss.SSS z" if cur_fmt == "%{time}%" else cur_fmt[7:-2],
            )
        elif cur_fmt.startswith("%{trace"):
            style = "clean" if cur_fmt == "%{trace}%" else cur_fmt[8:-2]

            if style == "bare":
                logging_string += (
                    f"{basename(record.frame.f_code.co_filename)}:"
                    f"{record.frame.f_lineno}"
                )
            elif style == "simple":
                logging_string += (
                    f"{record.global_name}@{record.frame.f_code.co_name}:"
                    f"{record.frame.f_lineno}"
                )
            elif style == "clean":
                logging_string += (
                    f"{_format_path(record.frame.f_code.co_filename)}@"
                    f"{record.frame.f_code.co_name}:{record.frame.f_lineno}"
                )
            elif style == "detailed":
                logging_string += " -> ".join(
                    f"{_format_path(trace.filename)}@{trace.name}:{trace.lineno}"
                    for trace in extract_stack(record.frame)
                )
            elif style == "full":
                logging_string += "\n{}\n".format("\n".join(format_stack(record.frame)))
            else:
                raise InvalidFormatSpecifierError(
                    f"Trace style {style!r} does not exist"
                )
        elif cur_fmt in ("%{gname}%", "%{global-name}%"):
            logging_string += record.global_name
        elif cur_fmt in ("%{pname}%", "%{process-name}%"):
            logging_string += record.process.name
        elif cur_fmt in ("%{pid}%", "%{process-identifier}%"):
            logging_string += str(record.process.ident)
        elif cur_fmt in ("%{tname}%", "%{thread-name}%"):
            logging_string += record.thread.name
        elif cur_fmt in ("%{tid}%", "%{thread-identifier}%"):
            logging_string += str(record.thread.ident)
        elif cur_fmt in ("%{msg}%", "%{message}%"):
            # stops infinite recursion when a message references itself
            if _from_msg:
                logging_string += record.message
            else:
                logging_string += _format(record.message, record, _from_msg=True)
        else:
            if not record.extra_info:
                raise InvalidFormatSpecifierError(
                    f"Format specifier {format_str!r} does not exist"
                )

            missing = object()
            info = record.extra_info.get(format_str, missing)
            if info is missing:
                raise InvalidFormatSpecifierError(
                    f"Format specifier {format_str!r} does not exist"
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

    Raises:
        - `InvalidFormatSpecifierError` - Raised if parser encounters an invalid format specifier.
    """
    assert isinstance(config.formatter, str)
    logging_string = _format(config.formatter, record)

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
