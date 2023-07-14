"""
_record.py:

This file contains all of the classes used for contructing `Record` objects.

Classes:
    - `Record` - Class used for storing runtime information collected by the logger.
"""

from dataclasses import dataclass
from datetime import datetime
from multiprocessing.process import BaseProcess
from threading import Thread
from traceback import StackSummary

from ._levels import Level


@dataclass(slots=True, frozen=True)
class Record:
    """
    Class used for storing runtime information collected by the logger.

    Attributes:
        - `logger_name: str` - Name of the logger which the record was produced by.
        - `global_name: str` - Global `__name__` from where the log was produced.
        - `level: Level` - Level/severity of the log.
        - `date_time: datetime` - Time & data of when the log was produced.
        - `stack_trace: StackSummary` - Stack trace of the currently executing frame where the
                                        log was produced.
        - `message: object` - Additional information which was added to the record.
        - `process: BaseProcess` - Currently executing process from where the log was produced.
        - `thread: Thread` - Currently executing thread from where the log was produced.
        - `exception: BaseException | None` - Optional exception to be printed.
    """

    logger_name: str
    global_name: str
    level: Level
    date_time: datetime
    stack_trace: StackSummary
    message: str
    process: BaseProcess
    thread: Thread
    exception: BaseException | None
