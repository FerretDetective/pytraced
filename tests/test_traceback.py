import traceback
from sys import _getframe as sys_getframe

from pytraced._traceback import _get_frame, _get_frame_fallback, extract_stack


def test_get_frame() -> None:
    test_normal = _get_frame()
    test_fallback = _get_frame_fallback()
    excepted = sys_getframe()

    assert test_normal.f_code.co_filename == excepted.f_code.co_filename
    assert test_normal.f_lineno == excepted.f_lineno
    assert test_normal.f_code.co_name == excepted.f_code.co_name

    assert test_fallback.f_code.co_filename == excepted.f_code.co_filename
    assert test_fallback.f_lineno == excepted.f_lineno
    assert test_fallback.f_code.co_name == excepted.f_code.co_name


def test_extract_stack() -> None:
    assert extract_stack(sys_getframe())[::-1] == traceback.extract_stack()
