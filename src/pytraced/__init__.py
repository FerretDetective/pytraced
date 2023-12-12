"""
pytraced:

version: 0.2.0

A simple, lightweight, & extensible logging library for python. This library provides an out of the
box logger which prints to `stderr`, however it is extremely customizable to fit a wide range of 
needs.

Globals:
    - `__version__` - The current version of this package.
    - `logger` - The default logger which prints to `stderr`.

Modules:
    - `colours` - The internal module which is used to adding colours to the terminal.

Classes:
    - `Logger` - Main class which manages the creation and dispatch of logs to its sinks.
    - `Level` - Class used for creating logging levels.
    - `LevelDoesNotExistError` - Error raised when trying to access a `Level` which does not exist.
    - `Sink` - Abstract base class from which all sinks must inherit.
    - `SinkDoesNotExistError` - Error raised when trying to access a `Sink` which does not exist.
    - `Config` - Class used for storing a logging configuration.
    - `Record` - Class used for storing runtime information collected by the logger.
    
Basic Usage:
A replacement for `print`:
    >>> from pytraced import logger
    >>> logger.info("this is a log")

Adding a new sink:
    >>> logger.add("logging.log")

Removing an old sink:
    >>> file_logger_id = logger.add("errors.log")
    >>> logger.remove(file_logger_id)

Customizing logs:
    >>> from sys import stderr
    >>> logger.remove(0)  # removes default `stderr`
    >>> logger.add(stderr, log_format="%{time:%x %X}% | %{lvl}% | %{trace:simple}% - %{msg}%")

Adding & use a new level:
    >>> from pytraced.colours import FgColour
    >>> level = logger.add_level("LEVEL", 15, [FgColour.BLUE])
    >>> logger.log(level, "Custom level")
    >>> logger.log("LEVEL", "Custom level")

Enabling/disabling the logger:
    >>> logger.disable()  # disable the current module
    >>> logger.enable()  # enable the current module
    >>> import some_module, some_module.submodule
    >>> logger.disable("some_module")  # disable "some_module" and all of its submodules
    >>> logger.enable("some_module")  # enable "some_module" and all of its non-overriden submodules
    >>> logger.disable("some_module.submodule")  # disable logs from "some_module.submodule"
    >>> logger.enable("some_module.submodule")  # enable logs from "some_module.submodule"
"""
from sys import stderr as _stderr

from . import colours
from ._config import Config
from ._levels import Level, LevelDoesNotExistError
from ._logger import Logger
from ._record import Record
from ._sink import Sink, SinkDoesNotExistError

__version__ = "0.2.0"
__all__ = (
    "logger",
    "Logger",
    "Level",
    "LevelDoesNotExistError",
    "Sink",
    "SinkDoesNotExistError",
    "Config",
    "Record",
    "colours",
)

logger = Logger("ROOT")
logger.add(_stderr)
