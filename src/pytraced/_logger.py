"""
_logger.py:

This file contains the main `Logger` class which manages the creation and dispatch of logs.

Classes:
    - `Logger` - Main class which manages the creation and dispatch of logs to its sinks.
"""
from __future__ import annotations

from atexit import register as atexit_register
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from multiprocessing import current_process
from os import PathLike
from pathlib import Path
from threading import current_thread
from typing import (
    TYPE_CHECKING,
    Callable,
    Generator,
    Iterable,
    Iterator,
    ParamSpec,
    TypeVar,
)

from ._config import Config
from ._levels import Level, LevelDoesNotExistError, get_defaults
from ._record import Record
from ._sink import Sink, SinkDoesNotExistError, SyncSink
from ._traceback import extract_stack, get_frame
from .colours import Colour, should_colourize, should_wrap, wrap

if TYPE_CHECKING:
    from _typeshed import OpenTextMode, StrPath, SupportsWrite

    P = ParamSpec("P")
    R = TypeVar("R")
    T = TypeVar("T")
    E = TypeVar("E", bound=BaseException)


class Logger:
    """
    Main class which manages the creation and dispatch of logs to its sinks.

    Attributes:
        - `name: str` - Name of the logger.

    Methods:
        - `log` - Write a log with a given level & message.
        - `info` - Write a log with a the level `INFO` and a given message.
        - `debug` - Write a log with a the level `DEBUG` and a given message.
        - `trace` - Write a log with a the level `TRACE` and a given message.
        - `success` - Write a log with a the level `SUCCESS` and a given message.
        - `warning` - Write a log with a the level `WARNING` and a given message.
        - `error` - Write a log with a the level `ERROR` and a given message.
        - `critical` - Write a log with a the level `CRITICAL` and a given message.
        - `log_exception` - Log an exception with a given level and additional information.
        - `log_func` - Decorator which logs arguments and return value of function calls.
        - `catch_func` - Decorator which logs errors that occur in the decorated function.
        - `catch_context` - Context manager which logs errors that occur in its body.
        - `add` - Add a new `Sink` to the logger with a custom configuration.
        - `remove` - Remove a previously added sink by its id.
        - `add_level` - Create and return a new level while making it available to the `Logger`.
        - `remove_level` - Remove an existing level.
        - `enable` - Enable logging for a specific module.
        - `disable` - Disable logging for a specific module.
    """

    __slots__ = "name", "_levels", "_sinks", "_disabled_for", "_sink_id_getter"

    def __init__(self, name: str) -> None:
        self.name = name
        self._levels = get_defaults()
        self._sinks: dict[int, Sink] = {}
        self._disabled_for: set[str] = set()
        self._sink_id_getter = self._sink_id_generator()
        atexit_register(self._close)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}{{ name: '{self.name}', levels: {self._levels}, "
            f"sinks: {self._sinks}, disabled_for: {self._disabled_for} }}"
        )

    def _sink_id_generator(self) -> Iterator[int]:
        """
        This is function returns an iterator which should be used to generate ids for all sinks.

        Returns: `Iterator[int]` - Iterator which produces unique ids for new sinks.
        """
        cur_id = 0
        while True:
            yield cur_id
            cur_id += 1

    def _close(self) -> None:
        """Iterate through all sinks and call their `close` method."""
        for sink in self._sinks.values():
            if sink.close is not None:
                sink.close()

    def _is_disabled_for(self, name: str) -> bool:
        """
        Check whether or not a module is disabled in the logger. Note that this also includes
        checks against parent modules.

        Parameters:
            - `name: str` - `__name__` of the module to check.

        Returns: `bool` - Whether or not the module is diabled.
        """
        mod_name, *parts = name.split(".")

        if mod_name in self._disabled_for:
            return True

        for sub_mod in parts:
            mod_name += "." + sub_mod
            if mod_name in self._disabled_for:
                return True

        return False

    def _log(
        self,
        level: str | Level,
        message: object,
        exception: BaseException | None = None,
        stack_level: int = 3,
    ) -> None:
        """
        Record a `Record` and propogate it to all of the `Logger`'s `Sink`s.

        Parameters:
            - `level: str | Level` - Severity of the log.
            - `message: object` - Message or additional information.
            - `exception: BaseException | None = None` - Optional exception to print with the log.
            - `stack_level: int = 3` - Int which stores how many calls back the logger called from.
        """
        frame = get_frame(stack_level)
        global_name: str = frame.f_globals["__name__"]

        if self._is_disabled_for(global_name):
            return

        if isinstance(level, str):
            if level not in self._levels:
                raise LevelDoesNotExistError(f"level {level!r} does not exist")

            level = self._levels[level]

        record = Record(
            self.name,
            global_name,
            level,
            datetime.now().astimezone(),
            extract_stack(frame),
            str(message),
            current_process(),
            current_thread(),
            exception,
        )

        for sink in self._sinks.values():
            if record.level.severity < sink.config.min_level or (
                sink.config.filter_func and not sink.config.filter_func(record)
            ):
                continue

            sink.write(sink.format(record))

    def log(self, level: str | Level, message: object) -> None:
        """
        Write a log with a given level & message.

        Parameters:
            - `level: str | Level` - String name of an existing level or a `Level` object.
            - `message: object` - Additional information to add to the log.
        """
        self._log(level, message)

    def info(self, message: object) -> None:
        """
        Write a log with a the level `INFO` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("INFO", message)

    def debug(self, message: object) -> None:
        """
        Write a log with a the level `DEBUG` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("DEBUG", message)

    def trace(self, message: object) -> None:
        """
        Write a log with a the level `TRACE` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("TRACE", message)

    def success(self, message: object) -> None:
        """
        Write a log with a the level `SUCCESS` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("SUCCESS", message)

    def warning(self, message: object) -> None:
        """
        Write a log with a the level `WARNING` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("WARNING", message)

    def error(self, message: object) -> None:
        """
        Write a log with a the level `ERROR` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("ERROR", message)

    def critical(self, message: object) -> None:
        """
        Write a log with a the level `CRITICAL` and a given message.

        Parameters:
            - `message: object` - Additional information to add to the log.
        """
        self._log("CRITICAL", message)

    def log_exception(
        self,
        exception: BaseException,
        message: object = (
            "Received error in process %{pname} (%{pid}%), "
            "on thread %{tname}% (%{tid}%)"
        ),
        level: str | Level = "ERROR",
    ) -> None:
        """
        Log an exception with a given level and additional information.

        Parameters:
            - `exception: BaseException` - Exception to log.
            - `message: object = ...` - Additional information to add to the log. Default
                                        information is the process's & thread's name and id.
            - `level: str | Level = "Error"` - String name of an existing level or a `Level` object.
        """
        self._log(level, message, exception)

    def log_func(
        self, level: str | Level
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Function decorator which logs the arguments and return value of a function whenever it is
        called.

        Parameters:
            - `level: str | Level` - String name of an existing level or a `Level` object.
        """

        def _decorator(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def _inner(*args: P.args, **kwargs: P.kwargs) -> R:
                self._log(
                    level,
                    f"Function {func.__name__!r} called with args: "
                    f"{args!r} and kwargs: {kwargs!r}",
                )
                res = func(*args, **kwargs)
                self._log(level, f"Function: {func.__name__!r} returned {res!r}")
                return res

            return _inner

        return _decorator

    def catch_func(
        self,
        message: object = (
            "An error has been caught in function '%{func}%', "
            "in process %{pname}% (%{pid}%), on thread %{tname}% (%{tid}%)"
        ),
        level: str | Level = "ERROR",
        default: T = None,  # type: ignore
        reraise: bool = False,
        exception_type: type[E] = Exception,  # type: ignore
        on_error: Callable[[E], None] | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R | T]]:
        """
        Function decorator which catches errors that occur during the execution of the decorated
        function.

        Parameters:
            - `message: object = ...` - Additional information to add to the log. Default
                                        information is the process's & thread's name and id.
            - `level: str | Level = "Error"` - String name of an existing level or a `Level` object.
            - `default: T = None` - Default value to return if an exception is caught.
            - `reraise: bool = False` - Whether or not to reraise exceptions that have been caught.
            - `exception_type: type[E] = Exception` - Exception type that will be caught.
            - `on_error: Callable[[E], None] | None = None` - Optional function that will be called
                                                              with the exception that was caught.
        """

        def _decorator(func: Callable[P, R]) -> Callable[P, R | T]:
            @wraps(func)
            def _inner(*args: P.args, **kwargs: P.kwargs) -> R | T:
                # pylint: disable=broad-exception-caught
                try:
                    return func(*args, **kwargs)
                except exception_type as exception:
                    self._log(
                        level,
                        str(message).replace("%{func}%", func.__name__),
                        exception,
                    )

                    if on_error is not None:
                        on_error(exception)

                    if reraise:
                        raise

                    return default

            return _inner

        return _decorator

    @contextmanager
    def catch_context(
        self,
        message: object = (
            "An error has been caught in a context manager, "
            "in process %{pname}% (%{pid}%), on thread %{tname}% (%{tid}%)"
        ),
        level: str | Level = "ERROR",
        reraise: bool = False,
        exception_type: type[E] = Exception,  # type: ignore
        on_error: Callable[[E], None] | None = None,
    ) -> Generator[None, None, None]:
        """
        Context manager which catches errors that occur during the execution of the body.

        Parameters:
            - `message: object = ...` - Additional information to add to the log. Default
                                        information is the process's & thread's name and id.
            - `level: str | Level = "Error"` - String name of an existing level or a `Level` object.
            - `reraise: bool = False` - Whether or not to reraise exceptions that have been caught.
            - `exception_type: type[E] = Exception` - Exception type that will be caught.
            - `on_error: Callable[[E], None] | None = None` - Optional function that will be called
                                                              with the exception that was caught.
        """
        try:
            yield
        except exception_type as exception:  # pylint: disable=broad-exception-caught
            self._log(level, message, exception, stack_level=4)

            if on_error is not None:
                on_error(exception)

            if reraise:
                raise

    def add(
        self,
        out: SupportsWrite[str] | Callable[[str], None] | StrPath,
        *,
        min_level: str | int | Level = 0,
        log_format: str | Callable[[Record], str] | Config = Config.DEFAULT,
        log_filter: Callable[[Record], bool] | None = None,
        colourize: bool = True,
        on_remove: Callable[[], None] | None = None,
        open_mode: OpenTextMode = "a",
        encoding: str = "utf-8",
    ) -> int:
        """
        Add a new `Sink` to the logger with a custom configuration.

        Format Secifiers for format strings:
            All format specifiers are wrapped in percent sign followed by braces; Exg: `%{lvl}%`.

            - `%{name}%` - Name of the logger from which the log was produced.
            - `%{lvl}%` or `%{level}%` - Level/severity of the log.
            - `%{time}%` - Datetime the log was produced at. To specify a specific datetime format
                           you can either use normal `strftime` formats or use to more user friendly
                           ones provided. `yyyy`: full year, `yy`: last digits of the year, `mm`:
                           zero-padded month, `dd`: zero-padded day, `HH`: zero-padded hour, `MM`:
                           zero-padded minute, `SS`: zero-padded seconds, `FS`: zero-padded
                           fractional seconds to three digits, `tzo`: timezone offset`, `tzn`:
                           timezone name. The format specifiers should be placed as follows:
                           `%{time:<...formats>}%`; Exg: `%{time:yy-mm-dd, %X}%`.
            - `%{trace}%` - Traceback from where the logger was called. To specify a specific trace
                            style you can use one of the defaults provided. `bare`: barebones
                            stack trace including only the filename and lineno (main.py:5),
                            `simple`: simple trace including the global `__name__`, the enclosing
                            fucntion, & the lineno (__main__@main:5), `clean`: simple yet
                            informative trace including relative path to the file, the enclosing
                            function, & the lineno (src/main.py@main:5), `detailed`: detailed stack
                            trace including the info provided by the `clean` info for entire
                            traceback (src/main.py@<module>:9 -> src/main.py@main:5), `full`: the
                            full unprocessed python traceback. Must follow the format
                            '%{trace:<format>}%'; Exg: '%{trace:clean}%'.
            - `%{gname}%` or `%{global-name}%` - Global `__name__` from where the log was produced.
            - `%{pname}%` or `%{process-name}%` - Name of the process where the log originated.
            - `%{pid}%` or `%{process-id}%` - Id of the process where the log originated.
            - `%{tname}%` or `%{thread-name}%` - Name of the thread where the log originated.
            - `%{tid}%` or `%{thread-id}%` - Id of the thread where the log originated.

        Parameters:
            - `out: SupportsWrite[str] | Callable[[str], None] | StrPath` - Output source for logs.
            - `min_level: str | int | Level = 0` - Minimum severity log that will be written.
            - `log_format: Callable[[Record], str]
                           | str | Config = Config.DEFAULT` - Should either be a parseable format
                                                              string or a function which returns a
                                                              formatted `Record`.
            - `log_filter: Callable[[Record], bool]
                           | None = None` - Function used to determine whether or not a log should
                                            be written to the stream. Returning false inidcates that
                                            a log shouldn't be written.
            - `colourize: bool = True` - Whether or not to colourize logs (if possible).
            - `on_remove: Callable[[], None]
                          | None = None` - Callback which will be called either when the sink is
                                           removed or when python intrepreter exits.
            - `open_mode: OpenTextMode = "a"` - Mode uesed to open a file (if applicable).
            - `encoding: str = "utf-8"` - File encoding used (if applicable).

        Returns: `int` - Id of the `Sink` object.
        """
        sink_id = next(self._sink_id_getter)

        if isinstance(out, Sink):
            self._sinks[sink_id] = out
            return sink_id

        if isinstance(out, (str, PathLike)):
            parent = Path(out).parent
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
            out = open(file=out, mode=open_mode, encoding=encoding)
            atexit_register(out.close)

        if isinstance(min_level, Level):
            min_level = min_level.severity
        elif isinstance(min_level, str):
            if (level := self._levels.get(min_level)) is None:
                raise LevelDoesNotExistError(
                    f"logging level of {min_level!r} does not exist"
                )
            min_level = level.severity

        if isinstance(log_format, Config):
            config = log_format
        else:
            config = Config(
                log_format=log_format,
                filter_func=log_filter,
                colourize=should_colourize(out) and colourize,
                min_level=min_level,
            )

        self._sinks[sink_id] = SyncSink(
            wrap(out) if should_wrap(out) else out, on_remove, config
        )

        return sink_id

    def remove(self, sink_id: int) -> None:
        """
        Call the `close` method of a previously added sink and remove it by its id.

        Parameters:
            - `sink_id: int` - Id of the sink to remove.

        Raises:
            - `SinkDoesExistError` - Raised if now sinks exists with the given id.
        """
        sink = self._sinks.get(sink_id)

        if sink is None:
            raise SinkDoesNotExistError(f"sink of id {sink_id!r} does not exist")

        if sink.close is not None:
            sink.close()

        del self._sinks[sink_id]

    def add_level(
        self, name: str, severity: int = 0, colours: Iterable[Colour] | None = None
    ) -> Level:
        """
        Create and return a new level while making it available to the `Logger`.

        Parameters:
            - `name: str` - Name of the level, note that this is also used to address the level.
            - `severity: int = 0` - Severity of the level, this is used to filter lower level logs.
            - `colours: Iterable[Colour] | None = None` - Colours that will be applied to the log.

        Returns: `Level` - The newly created level.
        """
        level = Level(name, severity, colours)
        self._levels[name] = level
        return level

    def remove_level(self, level: str | Level) -> None:
        """
        Remove an existing level.

        Parameters:
            - `level: str | Level` - String name of an existing level or a `Level` object.

        Raises:
            - `LevelDoesNotExistError` - Exception raised if the level is not found in the logger.
        """
        if isinstance(level, Level):
            level = level.name

        if level not in self._levels:
            raise LevelDoesNotExistError(f"level {level!r} does not exist")

        del self._levels[level]

    def enable(self, name: str | None = None) -> None:
        """
        Enable logging for a specific module.

        Parameters:
            - `name: str | None = None` - Name of the module to enable. If not the module where
                                          this method was called will be enable.
        """
        try:
            self._disabled_for.remove(name or get_frame(2).f_globals["__name__"])
        except KeyError:
            pass

    def disable(self, name: str | None = None) -> None:
        """
        Disable logging for a specific module.

        Parameters:
            - `name: str | None = None` - Name of the module to disable. If not the module where
                                          this method was called will be disabled.
        """
        self._disabled_for.add(name or get_frame(2).f_globals["__name__"])
