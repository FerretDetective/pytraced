from pytraced._levels import Level, LevelDoesNotExistError, get_defaults
from pytraced.colours import BgColour, FgColour


def test_level_creation() -> None:
    opts = "TEST", 10, (FgColour.BLACK, BgColour.WHITE)
    level = Level(*opts)
    assert level.name == opts[0]
    assert level.severity == opts[1]
    assert level.colours == opts[2]


def test_level_does_not_exist_error() -> None:
    assert issubclass(LevelDoesNotExistError, Exception)


def test_defaults() -> None:
    defaults = get_defaults()

    for name, level in defaults.items():
        assert name == level.name
