"""
_colouriser.py

This file contains the functions required to prepare strings with colours for the terminal.

Functions:
    - `add_colours` - Add colours a to strings and return the formatted string.
    - `should_colourize` - Check to see if an object should receive colourized strings.
    - `should_wrap` - Check to see if an object should be wrapped in a AnsiToWin32 converter.
    - `wrap` - Wrap a stream with a AnsiToWin32 wrapper.
"""

import os
import sys
from typing import TextIO, TypeGuard

from colorama.ansitowin32 import AnsiToWin32, StreamWrapper
from colorama.win32 import winapi_test

from ._colours import Colour, Meta


def _get_colours(*colours: Colour) -> str:
    """
    Returns a formatted string with the ansi codes corresponding to styles given.

    Parameters:
        - `*styles: Colour` - Styles to combine into a format string.

    Returns: `str` - Formatted string with the ansi code in place.
    """

    return "".join(f"\033[{style.value}m" for style in colours)


def add_colours(string: str, *colours: Colour, end: Colour | None = Meta.RESET) -> str:
    """
    Add colours % styles to strings and return the formatted string.

    Parameters:
        - `string: str` - String to add the colours & styles to.
        - `*colours: Colour` - Colours & styles to add to the string.
        - `end: Colour = Meta.RESET` - Style to append to the string, defaults to `Meta.RESET`
                                       which sets the colours back to the terminal default.

    Returns: `str` - String with the colours & styles added.
    """
    if end is None:
        return _get_colours(*colours) + string
    return _get_colours(*colours) + string + _get_colours(end)


def should_colourize(stream: object) -> bool:
    """
    Check to see if an object should receive colourized strings.

    Parameters:
        - `stream: object` - Object to check.

    Returns: `bool` Whether or not the object should receive colourized strings.
    """
    if stream in (sys.__stdout__, sys.__stderr__) and (
        "PYCHARM_HOSTED" in os.environ
        or (sys.platform == "win32" and "TERM" in os.environ)
    ):
        return True

    try:
        return stream.isatty()  # type: ignore
    except Exception:  # pylint: disable=broad-exception-caught
        return False


def should_wrap(stream: object) -> TypeGuard[TextIO]:
    """
    Check to see if an object should be wrapped in a AnsiToWin32 converter.

    Parameters:
        - `stream: object` - Object to check.

    Returns: `TypeGuard[TextIO]` - If true, the object returned is a TextIO that should be wrapped.
    """

    # Mypy will report an error for non-windows platforms because colorama-stubs annotates
    # `winapi_test: Callable[..., None]` whereas on windows it annotates it as
    # `winapi_test: Callable[[], bool]`. This therefore required the use of system dependant code.
    # In order to do so `sys.platform` was used because `platform.platform()` does not indicate
    # correctly to type checkers to ignore blocks conditionally based on the underlying operating
    # system
    if sys.platform == "win32" and stream in (sys.__stdout__, sys.__stderr__):
        return winapi_test()

    return False


def wrap(stream: TextIO) -> StreamWrapper:
    """
    Wrap a stream with a AnsiToWin32 wrapper.

    Parameters:
        - `stream: TextIO` - Stream to wrap.

    Returns: `StreamWrapper` - Stream wrapped in an AnsiToWin32 wrapper.
    """

    return AnsiToWin32(stream, convert=True, strip=False, autoreset=False).stream
