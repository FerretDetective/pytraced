from re import fullmatch

import py_tracer


def test_version() -> None:
    assert fullmatch(r"\d+\.\d+\.\d+", py_tracer.__version__)
