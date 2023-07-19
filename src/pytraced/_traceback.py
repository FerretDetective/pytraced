"""
_traceback.py:

This file contains all of the functions used for interating with Python stack frames.

Functions:
    - `get_frame` - Get the currently executing frame at a specified depth.
    - `extract_stack` - Get a `StackSummary` object from a `FrameType` object.
"""
from sys import exc_info
from traceback import StackSummary, walk_stack
from types import FrameType

# pylint: disable=broad-exception-caught, broad-exception-raised, protected-access, ungrouped-imports

try:
    from sys import _getframe

    def get_frame(depth: int = 0) -> FrameType:
        """
        Get the currently executing frame at a specified depth.

        Parameters:
            - `depth: int = 0` - Depth at which to return the frame.

        Returns: `FrameType` - Currently executing frame at the specified depth.
        """
        return _getframe(depth + 1)  # offset current frame

except ImportError:

    def get_frame(depth: int = 0) -> FrameType:
        """
        Fallback to get the currently executing frame if `sys._getframe` does not exist.

        Parameters:
            - `depth: int = 0` - Depth at which to return the frame.

        Returns: `FrameType` - Currently executing frame at the specified depth.
        """
        try:
            raise Exception
        except Exception:
            frame = exc_info()[2].tb_frame.f_back  # type: ignore
            for _ in range(depth):
                frame = frame.f_back  # type: ignore
            return frame  # type: ignore


def extract_stack(frame: FrameType) -> StackSummary:
    """
    Get a `StackSummary` object from a `FrameType` object.

    Parameters:
        - `frame: FrameType` - Frame from which to extrack the stack.

    Returns: `StackSummary` - StackSummary extracted from the frame.
    """
    return StackSummary.extract(walk_stack(frame), limit=None)
