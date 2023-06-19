from re import fullmatch

import pytraced


def test_version() -> None:
    assert fullmatch(r"\d+\.\d+\.\d+", pytraced.__version__)
