"""
_catcher.py:

This file contains the class used for catching and logging runtime errors.

Classes:
    - `Catcher` - Implementation of `ContextManager[None]` for catching & logging runtime errors.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Callable, Mapping

if TYPE_CHECKING:
    from ._levels import Level
    from ._logger import Logger


@dataclass(slots=True, frozen=True)
class Catcher(AbstractContextManager[None]):
    """
    This class is an implementation of `ContextManager[None]` and is designed to be used by the
    `Logger` to catch and log runtime exceptions.
    """

    from_decorator: bool
    logger: Logger
    message: object
    level: str | Level
    exc_types: type[BaseException] | tuple[type[BaseException], ...]
    exclude: type[BaseException] | tuple[type[BaseException], ...] | None
    reraise: bool
    on_error: Callable[[BaseException], None] | None
    extra_info: Mapping[str, object] | None

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        if exc_type is None:
            return None

        if not issubclass(exc_type, self.exc_types):
            return False

        if self.exclude is not None and issubclass(exc_type, self.exclude):
            return False

        self.logger._log(
            self.level,
            self.message,
            exc,
            self.extra_info,
            3 if self.from_decorator else 2,  # increase stack level for decorators
        )

        if self.on_error is not None:
            self.on_error(exc)  # type: ignore

        return not self.reraise
