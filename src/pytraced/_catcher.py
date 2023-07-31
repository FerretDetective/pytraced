"""
_catcher.py:

This file contains the class used for catching and logging runtime errors.

Classes:
    - `Catcher` - Implementation of `ContextManager[None]` for catching & logging runtime errors.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from ._levels import Level
    from ._logger import Logger

    E = TypeVar("E", bound=BaseException)


class Catcher(AbstractContextManager[None]):
    """
    This class is an implementation of `ContextManager[None]` and is designed to be used by the
    `Logger` to catch and log runtime exceptions.
    """

    __slots__ = (
        "from_decorator",
        "logger",
        "message",
        "level",
        "exception_type",
        "reraise",
        "on_error",
    )

    def __init__(
        self,
        from_decorator: bool,
        logger: Logger,
        message: object,
        level: str | Level,
        exception_type: type[E],
        reraise: bool,
        on_error: Callable[[E], None] | None,
    ) -> None:
        self.from_decorator = from_decorator
        self.logger = logger
        self.message = message
        self.level = level
        self.exception_type = exception_type
        self.reraise = reraise
        self.on_error = on_error

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"from_decorator={self.from_decorator!r}, "
            f"logger={self.logger!r}, "
            f"message={self.message!r}, "
            f"level={self.level!r}, "
            f"exception_type={self.exception_type!r}, "
            f"reraise={self.reraise!r}, "
            f"on_error={self.on_error!r})"
        )

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exception_type: type[E] | None,
        exception: E | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exception_type is None:
            return None

        if not issubclass(exception_type, self.exception_type):
            return False

        self.logger._log(
            self.level, self.message, exception, 3 if self.from_decorator else 2
        )

        if self.on_error is not None:
            self.on_error(exception)  # type: ignore

        return not self.reraise
