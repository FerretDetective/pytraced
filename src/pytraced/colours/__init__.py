"""
colours 1.0.0:

This package contains all of the needed functions & classes for printing colours to the terminal.

Functions:
    - `add_colours` - Function used to add colours to a string, adds the reset colour at the end.
    - `should_colourise` - Determine whether or an object should receive colourised strings.
    - `should_wrap` - Determine whether or an object should be wrapped with an AnsiToWin32 wrapper.
    - `wrap` - Return the stream wrapped in a AnsiToWin32 wrapper.

Enums:
    - `Colour` - Base class from which all colour enums inherit.
    - `Meta` - Meta styles like `BOLD` or `RESET`.
    - `FgColour` - Foreground text colours.
    - `BgColour` - Background text colours.
"""
from ._colouriser import add_colours, should_colourise, should_wrap, wrap
from ._colours import BgColour, Colour, FgColour, Meta

__version__ = "1.0.0"
__all__ = (
    "should_colourise",
    "should_wrap",
    "wrap",
    "add_colours",
    "Colour",
    "Meta",
    "BgColour",
    "FgColour",
)
