"""
_colours.py

This file contains all the enums needed for printing colours.

Enums:
    - `Colour` - Base class from which all colour enums inherit.
    - `Meta` - Meta styles like `BOLD` or `RESET`.
    - `FgColour` - Foregroud text colours.
    - `BgColour` - Background text colours.
"""
from enum import Enum


class Colour(Enum):
    """
    Base enum for which all colours are derived. This class serves no purpose
    other than to represent that all colours should be enums derived from this type.
    """


class Meta(Colour):
    """
    Meta Styles:
        - RESET,
        - BOLD,
        - DIM,
        - ITALIC,
        - UNDERLINE,
        - BLINK,
        - REVERSE,
        - STRIKE,
        - HIDE,
        - NORMAL,
    """

    RESET = 0
    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    REVERSE = 7
    STRIKE = 8
    HIDE = 9
    NORMAL = 22


class FgColour(Colour):
    """
    Foreground Colours:
        - BLACK,
        - RED,
        - GREEN,
        - YELLOW,
        - BLUE,
        - MAGENTA,
        - CYAN,
        - WHITE,

        - LIGHT_BLACK,
        - LIGHT_RED,
        - LIGHT_GREEN,
        - LIGHT_YELLOW,
        - LIGHT_BLUE,
        - LIGHT_MAGENTA,
        - LIGHT_CYAN,
        - LIGHT_WHITE,
    """

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    LIGHT_BLACK = 90
    LIGHT_RED = 91
    LIGHT_GREEN = 92
    LIGHT_YELLOW = 93
    LIGHT_BLUE = 94
    LIGHT_MAGENTA = 95
    LIGHT_CYAN = 96
    LIGHT_WHITE = 97


class BgColour(Colour):
    """
    Background Colours:
        - BLACK,
        - RED,
        - GREEN,
        - YELLOW,
        - BLUE,
        - MAGENTA,
        - CYAN,
        - WHITE,

        - LIGHT_BLACK,
        - LIGHT_RED,
        - LIGHT_GREEN,
        - LIGHT_YELLOW,
        - LIGHT_BLUE,
        - LIGHT_MAGENTA,
        - LIGHT_CYAN,
        - LIGHT_WHITE,
    """

    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47

    LIGHT_BLACK = 100
    LIGHT_RED = 101
    LIGHT_GREEN = 102
    LIGHT_YELLOW = 103
    LIGHT_BLUE = 104
    LIGHT_MAGENTA = 105
    LIGHT_CYAN = 106
    LIGHT_WHITE = 107
