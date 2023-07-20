from enum import Enum

from pytraced.colours import BgColour, Colour, FgColour, Meta


def test_base_class_derivation() -> None:
    assert issubclass(Meta, Colour)
    assert issubclass(FgColour, Colour)
    assert issubclass(BgColour, Colour)


def test_enums() -> None:
    assert issubclass(Colour, Enum)
    assert issubclass(Meta, Enum)
    assert issubclass(FgColour, Enum)
    assert issubclass(BgColour, Enum)


def test_types() -> None:
    for meta_colour in Meta:
        assert isinstance(meta_colour.value, int)

    for fg_colour in FgColour:
        assert isinstance(fg_colour.value, int)

    for bg_colour in BgColour:
        assert isinstance(bg_colour.value, int)
