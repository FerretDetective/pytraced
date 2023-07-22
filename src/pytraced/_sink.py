"""
_sink.py:

This file contains all of the classes used for constructing and interacting with `Sink` objects.

Classes:
    - `SinkDoesNotExistError` - Error raised when attempting to access a sink which does not exist.
    - `Sink` - Abstract base class from which all sinks must inherit.
    - `SyncSink` - Class used for blocking/synchronous logging.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ._config import Config
from ._formatter import format_record
from ._record import Record

if TYPE_CHECKING:
    from _typeshed import SupportsWrite


class SinkDoesNotExistError(Exception):
    """
    This class should be used to raise an error
    when trying to access a sink which does not exist.
    """


@dataclass(slots=True, frozen=True)
class Sink(ABC):
    """
    Abstract base class from which all sinks must inherit.

    Attributes:
        - `out: SupportsWrite[str] | Callable[[str], object]` - Destination of all formatted logs.
        - `close: Callable[[], None] | None` - Optional function which will be called when the sink
                                               is deregistered or close.

    Methods:
        - `format(record: Record) -> str` - Formats records for printing print
                                            based on the current config.

    Abstract Methods:
        - `write(string: str) -> None` - Should schedule the string to be written to the out.
    """

    out: SupportsWrite[str] | Callable[[str], object]
    close: Callable[[], None] | None
    config: Config

    def format(self, record: Record) -> str:
        """
        Takes in a `Record` instance and returns the formatted
        string reading for logging to the out.

        Parameters:
            - `record: Record` - Record from which a logging string will be produced.

        Returns: `str` - Formatted string for logging.
        """
        if callable(self.config.formatter):
            return self.config.formatter(record)
        return format_record(record, self.config)

    @abstractmethod
    def write(self, string: str) -> None:
        """
        Concrete implementations of this method should schedule the
        string to be written to the out.

        Parameters:
            - `string: str` - String to be written to the out.
        """


class SyncSink(Sink):
    """
    Class used for blocking/synchronous logging.

    Attributes:
        - `out: SupportsWrite[str] | Callable[[str], object]` - Destination of all formatted logs.
        - `close: Callable[[], None] | None` - Optional function which will be called when the sink
                                               is deregistered or close.

    Methods:
        - `format(record: Record) -> str` - Formats records for printing print
                                            based on the current config.
        - `write(string: str) -> None` - Directly writes to string to the out.
    """

    __slots__ = ()

    def write(self, string: str) -> None:
        """
        Directly writes to string to the out.

        Parameters:
            - `string: str` - String to be written to the out.
        """
        if not callable(self.out):
            self.out.write(string)
        else:
            self.out(string)
