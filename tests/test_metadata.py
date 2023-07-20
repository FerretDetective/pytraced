from re import fullmatch

import pytraced


def test_version() -> None:
    assert fullmatch(r"\d+\.\d+\.\d+", pytraced.__version__)


def test_all() -> None:
    assert "logger" in pytraced.__all__
    assert "Logger" in pytraced.__all__
    assert "Level" in pytraced.__all__
    assert "LevelDoesNotExistError" in pytraced.__all__
    assert "Sink" in pytraced.__all__
    assert "SinkDoesNotExistError" in pytraced.__all__
    assert "Config" in pytraced.__all__
    assert "Record" in pytraced.__all__
    assert "colours" in pytraced.__all__
