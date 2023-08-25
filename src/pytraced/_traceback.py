"""
_traceback.py:

This file contains all of the functions used for interacting with Python stack frames.

Functions:
    - `get_frame` - Get the currently executing frame at a specified depth.
    - `extract_stack` - Get a `StackSummary` object from a `FrameType` object.
"""
import sys
from types import FrameType

# pylint: disable=broad-exception-caught, broad-exception-raised, protected-access, ungrouped-imports


def _get_frame(depth: int = 0) -> FrameType:
    """
    Get the currently executing frame at a specified depth.

    Parameters:
        - `depth: int = 0` - Depth at which to return the frame.

    Returns: `FrameType` - Currently executing frame at the specified depth.
    """
    return sys._getframe(depth + 1)  # offset current frame


def _get_frame_fallback(depth: int = 0) -> FrameType:
    """
    Fallback to get the currently executing frame if `sys._getframe` does not exist.

    Parameters:
        - `depth: int = 0` - Depth at which to return the frame.

    Returns: `FrameType` - Currently executing frame at the specified depth.
    """

    try:
        raise Exception
    except Exception:
        frame: FrameType = sys.exc_info()[2].tb_frame  # type: ignore
        for _ in range(depth + 1):  # offset current frame
            frame: FrameType = frame.f_back  # type: ignore
        return frame


get_frame = _get_frame if hasattr(sys, "_getframe") else _get_frame_fallback


def extract_error_frame(exc: BaseException) -> FrameType:
    """
    Return the frame where where the exception `exc` was raised.

    Parameters:
        - `exc: BaseException` - Exception to retrieve the frame from.

    Returns: `FrameType` - Frame where the exception was raised.

    Raises:
        - `ValueError` - Raised if `exc.__traceback__` is None as frame cannot be extract.
    """
    if exc.__traceback__ is None:
        raise ValueError(f"cannot extract frame from {exc!r}, '__traceback__' is None")

    tb = exc.__traceback__
    while tb.tb_next is not None:
        tb = tb.tb_next

    return tb.tb_frame
