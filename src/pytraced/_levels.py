"""
_levels.py:

This file contains all of the classes & functions used for contructing 
and interacting with Level objects.

Classes:
    - `LevelDoesNotExistError` - Error raised when attemping to access a Level which does not exist.
    - `Level` - Class used for creating logging levels.

Functions:
    - `get_defaults` - Return a copy of the default levels in a mapping between their name and the 
                       `Level` object.
"""
from dataclasses import dataclass, field
from typing import Iterable

from .colours import BgColour, Colour, FgColour


class LevelDoesNotExistError(Exception):
    """
    This class should be used to raise an error
    when trying to access a Level which does not exist.
    """


@dataclass(slots=True, frozen=True)
class Level:
    """
    Class used for creating logging levels.

    Attributes:
        - `name: str` - Name of the level, note that this is used to lookup the level.
        - `severity: int` - Severity of logging. Used to filter logs based on severity.
        - `colours: Iterable[Colour] | None = None` - Optional colours which will be added to logs
                                                      when printed to any stream where
                                                      `stream.isatty()` is True.
    """

    name: str
    severity: int
    colours: Iterable[Colour] | None = field(default=None)


def get_defaults() -> dict[str, Level]:
    """
    Return a copy of the default levels in a mapping between their name and the `Level` object.

    Default Levels:
        - 00 : LOG
        - 10 : INFO
        - 20 : DEBUG
        - 30 : TRACE
        - 40 : SUCCESS
        - 50 : WARNING
        - 60 : ERROR
        - 70 : CRITICAL

    Returns: `dict[str, Level]` - Copy of the default levels as described above.
    """
    return {
        "LOG": Level("LOG", 0),
        "INFO": Level("INFO", 10, (FgColour.CYAN,)),
        "DEBUG": Level("DEBUG", 20, (FgColour.BLUE,)),
        "TRACE": Level("TRACE", 30, (FgColour.MAGENTA,)),
        "SUCCESS": Level("SUCCESS", 40, (FgColour.LIGHT_GREEN,)),
        "WARNING": Level("WARNING", 50, (FgColour.LIGHT_YELLOW,)),
        "ERROR": Level("ERROR", 60, (FgColour.LIGHT_RED,)),
        "CRITICAL": Level("CRITICAL", 70, (FgColour.LIGHT_RED, BgColour.RED)),
    }
