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
from typing import TYPE_CHECKING, Callable, Iterable, Mapping

if TYPE_CHECKING:
    from ._levels import Level
    from ._logger import Logger


def _issubclass(class_: type, classes: type | Iterable[type]) -> bool:
    """
    Check if `class_` is a subclass of `classes`. Notably different in that it accepts an
    iterable of types rather than a tuple like `builtins.issubclass`

    Parameters:
        - `class_`: Class or type to check
        - `classes`: Class, classes, or types to check against

    Returns: Whether or not `class_` is a subclass of `classes`
    """
    if hasattr(classes, "__iter__") and callable(classes.__iter__):
        return issubclass(class_, tuple(classes))
    return issubclass(class_, classes)  # type: ignore


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
    exc_types: type[BaseException] | Iterable[type[BaseException]]
    exclude: type[BaseException] | Iterable[type[BaseException]] | None
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

        if not _issubclass(exc_type, self.exc_types):
            return False

        if self.exclude is not None and _issubclass(exc_type, self.exclude):
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
