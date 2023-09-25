"""
_logger.py:

This file contains the main `Logger` class which manages the creation and dispatch of logs.

Classes:
    - `Logger` - Main class which manages the creation and dispatch of logs to its sinks.
"""
from __future__ import annotations

from atexit import register as atexit_register
from datetime import datetime
from functools import partial, update_wrapper
from inspect import (
    isasyncgenfunction,
    isclass,
    iscoroutinefunction,
    isgeneratorfunction,
)
from multiprocessing import current_process
from os import PathLike
from pathlib import Path
from sys import exc_info
from threading import current_thread
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    ContextManager,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    ParamSpec,
    TypeVar,
    overload,
)

from ._catcher import Catcher
from ._config import Config
from ._levels import Level, LevelDoesNotExistError, get_defaults
from ._record import Record
from ._sink import Sink, SinkDoesNotExistError, SyncSink
from ._traceback import extract_error_frame, get_frame
from .colours import Colour, should_colourise, should_wrap, wrap

if TYPE_CHECKING:
    from _typeshed import OpenTextMode, StrPath, SupportsWrite

    P = ParamSpec("P")
    R = TypeVar("R")
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

        Returns: `bool` - Whether or not the module is disabled.
        """
        if not self._disabled_for:
            return False

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
        extra_info: Mapping[str, object] | None = None,
        stack_level: int = 2,
    ) -> None:
        """
        Create a `Record` and propagate it to all of the `Logger`'s `Sink`s.

        Parameters:
            - `level: str | Level` - Severity of the log.
            - `message: object` - Message or additional information.
            - `exception: BaseException | None = None` - Optional exception to print with the log.
            - `stack_level: int = 2` - Int which stores how many calls back the logger called from.

        Raises:
            - `LevelDoesNotExistError` - Raised if a string level does not exist.
        """
        if not self._sinks.values():
            return

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
            datetime.now(),
            frame,
            str(message),
            current_process(),
            current_thread(),
            extra_info,
            exception,
        )

        for sink in self._sinks.values():
            if record.level.severity < sink.config.min_level or (
                sink.config.filter_func is not None
                and not sink.config.filter_func(record)
            ):
                continue

            sink.write(sink.format(record))

    def log(self, level: str | Level, message: object) -> None:
        """
        Write a log with a given level & message.

        Parameters:
            - `level: str | Level` - String name of an existing level or a `Level` object.
            - `message: object` - Additional information to add to the log.

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
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

    def exception(
        self,
        exception: BaseException,
        level: str | Level = "ERROR",
        message: object = (
            "Received error in process '%{pname}%' (%{pid}%), "
            "on thread '%{tname}%' (%{tid}%)"
        ),
    ) -> None:
        """
        Log an exception with a given level and additional information.

        Parameters:
            - `exception: BaseException` - Exception to log.
            - `level: str | Level` - String name of an existing level or a `Level` object.
            - `message: object` - Additional information to add to the log. Default information is
                                  the process's & thread's name and id.

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
        """
        self._log(level, message, exception)

    def log_func(
        self, level: str | Level
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Function decorator which logs the arguments and return value of a function whenever it is
        called. This decorator works for any callable which is a function, async function,
        generator, or aysnc generator.

        Parameters:
            - `level: str | Level` - String name of an existing level or a `Level` object.

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
        """

        def _decorator(func: Callable[P, R]) -> Callable[P, R]:
            if isgeneratorfunction(func):

                def _log_wrapper(
                    *args: P.args, **kwargs: P.kwargs
                ) -> Generator[Any, Any, Any]:
                    self._log(
                        level,
                        f"Generator {func.__name__!r} called with args: "
                        f"{args!r} and kwargs: {kwargs!r}",
                    )

                    # The following code is semantically equivalent to "yield from".
                    # More info: https://peps.python.org/pep-0380/#formal-semantics
                    gen = func(*args, **kwargs)
                    try:
                        yielded = next(gen)
                        received = None

                        while True:
                            self._log(
                                level,
                                f"Generator {func.__name__!r} yielded {yielded!r}"
                                f" and was sent {received!r}",
                            )

                            try:
                                received = yield yielded

                                try:
                                    if received is None:
                                        yielded = next(gen)
                                    else:
                                        yielded = gen.send(received)
                                except StopIteration as stop_iter:
                                    stop_iter_val = stop_iter.value
                                    break
                            except GeneratorExit as gen_exit:
                                if hasattr(gen, "close") and callable(gen.close):
                                    gen.close()
                                raise gen_exit
                            except BaseException as exc:
                                if not hasattr(gen, "throw") or not callable(gen.throw):
                                    raise exc

                                try:
                                    yielded = gen.throw(*exc_info())
                                except StopIteration as stop_iter:
                                    stop_iter_val = stop_iter.value
                                    break
                    except StopIteration as stop_iter:
                        stop_iter_val = stop_iter.value

                    # pylint: disable=used-before-assignment
                    self._log(
                        level,
                        f"Generator {func.__name__!r} exhausted with value {stop_iter_val!r}",
                    )
                    return stop_iter_val

            elif isasyncgenfunction(func):

                async def _log_wrapper(  # type: ignore[misc]
                    *args: P.args, **kwargs: P.kwargs
                ) -> AsyncGenerator[Any, Any]:
                    self._log(
                        level,
                        f"Async Generator {func.__name__!r} called with args: "
                        f"{args!r} and kwargs: {kwargs!r}",
                    )

                    # The following code is semantically equivalent to "yield from".
                    # More info: https://peps.python.org/pep-0380/#formal-semantics
                    gen = func(*args, **kwargs)
                    try:
                        yielded = await anext(gen)
                        received = None

                        while True:
                            self._log(
                                level,
                                f"Async Generator {func.__name__!r} yielded {yielded!r}"
                                f" and was sent {received!r}",
                            )

                            try:
                                received = yield yielded

                                try:
                                    if received is None:
                                        yielded = await anext(gen)
                                    else:
                                        yielded = await gen.asend(received)
                                except StopAsyncIteration:
                                    break
                            except GeneratorExit as gen_exit:
                                if hasattr(gen, "aclose") and callable(gen.aclose):
                                    await gen.aclose()
                                raise gen_exit
                            except BaseException as exc:
                                # XXX: reimplement if possible
                                # Check if the exception was raised in the subgenerator, if so
                                # reraise it instead of sending it back with `athrow`. This is done
                                # because (as of writing) exceptions raised during the excution of
                                # the subgenerator will not bubble up to the caller if thrown back
                                # to the subgenerator as is the case with normal generators.
                                if (
                                    extract_error_frame(exc).f_code.co_name
                                    == func.__name__
                                ):
                                    raise exc

                                if not hasattr(gen, "athrow") or not callable(
                                    gen.athrow
                                ):
                                    raise exc

                                try:
                                    yielded = await gen.athrow(*exc_info())
                                except StopAsyncIteration:
                                    break
                    except StopAsyncIteration:
                        pass

                    # pylint: disable=used-before-assignment
                    self._log(
                        level,
                        f"Async Generator {func.__name__!r} exhausted",
                    )

            elif iscoroutinefunction(func):

                async def _log_wrapper(  # type: ignore[misc]
                    *args: P.args, **kwargs: P.kwargs
                ) -> Any:
                    self._log(
                        level,
                        f"Async function {func.__name__!r} called with args: "
                        f"{args!r} and kwargs: {kwargs!r}",
                    )
                    res = await func(*args, **kwargs)
                    self._log(
                        level, f"Async function {func.__name__!r} returned {res!r}"
                    )
                    return res

            else:

                def _log_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:  # type: ignore[misc]
                    self._log(
                        level,
                        f"Function {func.__name__!r} called with args: "
                        f"{args!r} and kwargs: {kwargs!r}",
                    )
                    res = func(*args, **kwargs)
                    self._log(level, f"Function: {func.__name__!r} returned {res!r}")
                    return res

            update_wrapper(_log_wrapper, func)
            return _log_wrapper  # type: ignore[return-value]

        return _decorator

    @overload
    def catch_func(  # type: ignore[misc]
        self,
        exception: (type[BaseException] | Iterable[type[BaseException]]) = Exception,
        exclude: type[BaseException] | Iterable[type[BaseException]] | None = None,
        default: object = None,
        reraise: bool = False,
        level: str | Level = "ERROR",
        on_error: Callable[[BaseException], None] | None = None,
        message: object = (
            "An error has been caught in %{ftype}% '%{fname}%', "
            "in process '%{pname}%' (%{pid}%), on thread '%{tname}%' (%{tid}%)"
        ),
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        ...

    @overload
    def catch_func(self, exception: Callable[P, R]) -> Callable[P, R]:
        ...

    def catch_func(
        self,
        exception: (type[BaseException] | Iterable[type[BaseException]])
        | Callable[P, R] = Exception,
        exclude: type[BaseException] | Iterable[type[BaseException]] | None = None,
        default: object = None,
        reraise: bool = False,
        level: str | Level = "ERROR",
        on_error: Callable[[BaseException], None] | None = None,
        message: object = (
            "An error has been caught in %{ftype}% '%{fname}%', "
            "in process '%{pname}%' (%{pid}%), on thread '%{tname}%' (%{tid}%)"
        ),
    ) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
        """
        Function decorator which catches errors that occur during the execution of the decorated
        function. This decorator works for any callable which is a function, async function,
        generator, or aysnc generator.

        Parameters:
            - `exception` - Exception type(s) that will be caught.
            - `exclude` - Exception type(s) that will be excluded.
            - `default` - Default value to return if an exception is caught.
            - `reraise` - Whether or not to reraise exceptions that have been caught.
            - `level` - String name of an existing level or a `Level` object, default is 'ERROR'.
            - `on_error` - Optional function that will be called with the exception that was caught.
            - `message` - Additional information to add to the log. Default information is the
                          process's & thread's name and id.

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
        """
        if (
            not isclass(exception) or not issubclass(exception, BaseException)
        ) and callable(exception):
            return self.catch_func()(exception)  # type: ignore

        def _decorator(func: Callable[P, R]) -> Callable[P, R]:
            catcher = partial(
                Catcher,
                True,
                self,
                message,
                level,
                exception,
                exclude,
                reraise,
                on_error,
            )

            extra_info = {"%{fname}%": func.__name__}

            if isgeneratorfunction(func):
                extra_info["%{ftype}%"] = "Generator"

                def _catch_wrapper(
                    *args: P.args, **kwargs: P.kwargs
                ) -> Generator[Any, Any, Any]:
                    with catcher(extra_info):
                        return (yield from func(*args, **kwargs))
                    return default

            elif isasyncgenfunction(func):
                extra_info["%{ftype}%"] = "Async Generator"

                async def _catch_wrapper(  # type: ignore[misc]
                    *args: P.args, **kwargs: P.kwargs
                ) -> AsyncGenerator[Any, Any]:
                    # pylint: disable=line-too-long

                    with catcher(extra_info):
                        # Async "yield from" does not exist so the following is the semantic equivalent.
                        # No async "yield from": https://peps.python.org/pep-0525/#asynchronous-yield-from
                        # "yield from" semantic equivalent: https://peps.python.org/pep-0380/#formal-semantics
                        gen = func(*args, **kwargs)
                        try:
                            yielded = await anext(gen)

                            while True:
                                try:
                                    received = yield yielded

                                    try:
                                        if received is None:
                                            yielded = await anext(gen)
                                        else:
                                            yielded = await gen.asend(received)
                                    except StopAsyncIteration:
                                        break
                                except GeneratorExit as gen_exit:
                                    if hasattr(gen, "aclose") and callable(gen.aclose):
                                        await gen.aclose()

                                    raise gen_exit
                                except BaseException as exc:
                                    # XXX: reimplement if possible
                                    # Check if the exception was raised in the subgenerator,
                                    # if so reraise it instead of sending it back with `athrow`.
                                    # This is done because (as of writing) exceptions raised during
                                    # the excution of the subgenerator will not bubble up to the caller if
                                    # thrown back to the subgenerator as is the case with normal
                                    # generators.
                                    if (
                                        extract_error_frame(exc).f_code.co_name
                                        == func.__name__
                                    ):
                                        raise exc

                                    if not hasattr(gen, "athrow") or not callable(
                                        gen.athrow
                                    ):
                                        raise exc

                                    try:
                                        yielded = await gen.athrow(*exc_info())
                                    except StopAsyncIteration:
                                        break
                        except StopAsyncIteration:
                            pass

            elif iscoroutinefunction(func):
                extra_info["%{ftype}%"] = "Async Function"

                async def _catch_wrapper(  # type: ignore[misc]
                    *args: P.args, **kwargs: P.kwargs
                ) -> Any:
                    with catcher(extra_info):
                        return await func(*args, **kwargs)
                    return default

            else:
                extra_info["%{ftype}%"] = "Function"

                def _catch_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:  # type: ignore[misc]
                    with catcher(extra_info):
                        return func(*args, **kwargs)
                    return default

            update_wrapper(_catch_wrapper, func)
            return _catch_wrapper  # type: ignore[return-value]

        return _decorator

    def catch_context(
        self,
        exception: type[BaseException] | Iterable[type[BaseException]] = Exception,
        exclude: type[BaseException] | Iterable[type[BaseException]] | None = None,
        reraise: bool = False,
        level: str | Level = "ERROR",
        on_error: Callable[[BaseException], None] | None = None,
        message: object = (
            "An error has been caught in a ContextManager, "
            "in process '%{pname}%' (%{pid}%), on thread '%{tname}%' (%{tid}%)"
        ),
    ) -> ContextManager[None]:
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

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
        """
        return Catcher(
            False, self, message, level, exception, exclude, reraise, on_error, None
        )

    def add(
        self,
        out: SupportsWrite[str] | Callable[[str], None] | StrPath,
        *,
        min_level: str | int | Level = 0,
        log_format: str | Callable[[Record], str] | Config = Config.DEFAULT_FORMAT,
        log_filter: Callable[[Record], bool] | None = None,
        colourise: bool = True,
        on_remove: Callable[[], None] | None = None,
        open_mode: OpenTextMode = "a",
        encoding: str = "utf-8",
    ) -> int:
        """
        Add a new `Sink` to the logger with a custom configuration. If given a subclass of `Sink`
        skip all configuration and add the existing sink.

        Format specifiers for log format strings:
            All format specifiers are wrapped in percent sign followed by braces, exg: `%{lvl}%`.

            - `name` - Name of the logger from which the log was produced.
            - `lvl` or `level` - Level/severity of the log.
            - `time` - Datetime the log was produced at. Datetime format specifiers listed below.
                       Must adhere to the following format: `time:<datetime-fmt>`,
                       exg: `time:YYYY/MM/DD`. Default format is ISO time.
            - `trace` - Traceback from where the logger was called. Trace styles are listed below.
                        Must adhere to the following format: `trace:<trace-style>`,
                        exg: `trace:clean`. Default format is `clean`.
            - `gname` or `global-name` - Global `__name__` from where the log was produced.
            - `pname` or `process-name` - Name of the process where the log originated.
            - `pid` or `process-identifier` - Id of the process where the log originated.
            - `tname` or `thread-name` - Name of the thread where the log originated.
            - `tid` or `thread-id` - Id of the thread where the log originated.

        Datetime format specifiers:
            - `YYYY` - Full year [1-9999]. Exg: '1234'.
            - `YY` - Last two digits of the year [0, 99]. Exg: '34'.
            - `Q` - Quarter [1, 4]. Exg: '1'.
            - `MMMM` - Month name [January, December]. Exg: 'February'.
            - `MMM` - Month name abbreviation [Jan, Dec]. Exg: 'Feb'.
            - `MM` - Zero-padded month number [01, 12]. Exg: '02'.
            - `M` - Month number [1, 12]. Exg: '2'.
            - `DDDD` - Zero-padded day of the year [001, 366]. Exg: '032'.
            - `DDD` - Day of the year [1, 366]. Exg: '32'.
            - `DD` - Zero-padded day of the month [01, 31]: Exg: '01'.
            - `D` - Day of the month [1, 31]. Exg: '1'.
            - `ddd` - Day name [Monday, Sunday]. Exg: 'Monday'.
            - `dd` - Day name abbreviation [Mon, Sun]. Exg: 'Mon'.
            - `d` - Day of the week [0, 6]. Exg: '0'.
            - `A` - AM or PM [AM, PM]. Exg: 'AM'.
            - `HH` - Zero-padded 12 hour [01, 12]. Exg: '01'.
            - `H` - 12 hour [1, 12]. Exg: '1'.
            - `hh` - Zero-padded 24 hour [01, 24]. Exg: '01'.
            - `h` - 24 hour [1, 24]. Exg: '1'.
            - `mm` - Zero-padded minute [00, 59]. Exg: '01'.
            - `m` - Minute [0, 59]. Exg: '1'.
            - `ss` - Zero-padded second [00, 59]. Exg: '01'.
            - `s` - Second [0, 59]. Exg: '1'.
            - `[S, SSSSSS]` - Zero-padded n-digits of fraction second time, one 'S' represents one
                              digit [000000, 999999]. Exg: '012085'.
            - `Z` - Local timezone name. Exg: 'Mountain Standard Time'.
            - `z` - Local to UTC timezone offset. Exg: '-0600'.
            - `X` - Seconds or POSIX timestamp. Exg: '1695359774.25476'.
            - `x` - Microseconds timestamp. Exg: '1695359857663486'.

        Traceback styles:
            - `bare` - Includes only the filename and line number. Exg: 'main.py:5'.
            - `simple` - Includes the global `__name__`, the enclosing function, & the line number.
                         Exg: '__main__@main:5'.
            - `clean` - Includes relative path to the file, the enclosing function, & the line
                        number. Exg: 'src/main.py@main:5'
            - `detailed` - Includes the information from `clean` for the entire stack trace.
                           Exg: 'src/main.py@<module>:9 -> src/main.py@main:5'.
            - `full` - Full, unchanged python traceback.

        Parameters:
            - `out` - Output source for logs.
            - `min_level` - Minimum severity log that will be written.
            - `log_format` - Should either be a parsable format string or a function which returns
                             a formatted `Record`.
            - `log_filter` - Function used to determine whether or not a log should be written to
                             the stream. Returning false indicates that a log shouldn't be written.
            - `colourise` - Whether or not to colourise logs (if possible).
            - `on_remove` - Callback which will be called either when the sink is removed or when
                            python interpreter exits.
            - `open_mode` - Mode used to open a file (if applicable).
            - `encoding` - File encoding used (if applicable).

        Returns: Id of the `Sink` object.

        Raises:
            - `LevelDoesNotExistError` - Raised if a given string level name does not exist.
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
            level = self._levels.get(min_level)
            if level is None:
                raise LevelDoesNotExistError(
                    f"Logging level {min_level!r} does not exist"
                )
            min_level = level.severity

        if not isinstance(log_format, Config):
            log_format = Config(
                log_format, log_filter, should_colourise(out) and colourise, min_level
            )

        self._sinks[sink_id] = SyncSink(
            wrap(out) if should_wrap(out) else out, on_remove, log_format
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
            self._disabled_for.remove(name or get_frame(1).f_globals["__name__"])
        except KeyError:
            pass

    def disable(self, name: str | None = None) -> None:
        """
        Disable logging for a specific module.

        Parameters:
            - `name: str | None = None` - Name of the module to disable. If not the module where
                                          this method was called will be disabled.
        """
        self._disabled_for.add(name or get_frame(1).f_globals["__name__"])
