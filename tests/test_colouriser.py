import os
import sys
from io import StringIO
from platform import platform

from pytraced.colours import (
    FgColour,
    Meta,
    add_colours,
    should_colourise,
    should_wrap,
    wrap,
)


def test_add_colours() -> None:
    string = "test"
    colour = FgColour.RED
    expected = f"\033[{colour.value}m{string}"

    assert add_colours(string, colour) == f"{expected}\033[{Meta.RESET.value}m"
    assert add_colours(string, colour, end=None) == expected


def test_should_colourise() -> None:
    class Dummy:
        def isatty(self) -> bool:
            return True

    assert should_colourise(Dummy())
    assert not should_colourise(object())

    tmp_environ = os.environ
    tmp_platform = sys.platform

    os.environ["TERM"] = "TESTING"
    sys.platform = "win32"

    assert should_colourise(sys.__stderr__)

    os.environ = tmp_environ
    sys.platform = tmp_platform


def test_should_wrap() -> None:
    tmp_platform = sys.platform
    sys.platform = "win32"
    assert bool(should_wrap(sys.__stderr__)) is (platform() == "Windows")
    sys.platform = tmp_platform


def test_wrap() -> None:
    string = "TESTING"
    wrapped = wrap(StringIO())
    wrapped.write(add_colours(string, FgColour.WHITE))
