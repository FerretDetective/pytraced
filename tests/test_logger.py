from asyncio import run
from random import choices, randint, sample
from string import ascii_letters
from typing import AsyncIterator, Iterator

from pytest import raises

from pytraced import Level, LevelDoesNotExistError, Logger, SinkDoesNotExistError
from pytraced._levels import get_defaults
from pytraced.colours import FgColour

from .conftest import DummySink, get_config, get_stringio_logger

# pylint: disable=protected-access


def test_creation() -> None:
    logger = Logger("TEST")
    assert logger.name == "TEST"
    assert logger._levels == get_defaults()
    assert not logger._sinks
    assert not logger._disabled_for
    assert next(logger._sink_id_getter) == 0


def test_repr() -> None:
    logger = Logger("TEST")
    assert repr(logger) == "Logger(name='TEST')"


def test_id_getter() -> None:
    logger = Logger("TEST")
    for expected, received in zip(range(100), logger._sink_id_getter, strict=False):
        assert expected == received


def test_close() -> None:
    was_closed = False

    def close() -> None:
        nonlocal was_closed
        was_closed = True

    logger = Logger("TEST")
    logger.add(DummySink(lambda _: None, close, get_config("%{msg}%")))
    logger._close()

    assert was_closed


def test_is_disabled_for() -> None:
    logger = Logger("TEST")

    names = [
        ".".join(
            "".join(choices(ascii_letters, k=randint(1, 25)))  # length of each part
            for _ in range(randint(1, 15))  # number of parts
        )
        for _ in range(1_000)  # number of names
    ]

    # take a random sample the of the names and disable on a random mod depth
    for mod_name in sample(names, k=randint(len(names) // 5, len(names))):
        parts = mod_name.split(".")
        logger._disabled_for.add(".".join(parts[: randint(1, len(parts))]))

    def correct() -> set[str]:
        skipped: set[str] = set()
        for name in names:
            parts: list[str] = []

            for part in name.split("."):
                parts.append(part)
                mod_name = ".".join(parts)

                if mod_name in logger._disabled_for:
                    skipped.add(name)
                    break

        return skipped

    assert not correct().difference(filter(logger._is_disabled_for, names))


def test_priv_log() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    # skip disabled
    logger.disable(__name__)
    logger._log("LOG", "message", stack_level=1)
    logger.enable(__name__)
    io.seek(0)
    assert not io.read()

    # verify error is raised with invalid string level
    with raises(LevelDoesNotExistError):
        logger._log("does-not-exist", "message", stack_level=1)

    # test skipping based on min_level and log_filter
    logger.remove(0)
    logger.add(io, min_level=50, log_filter=lambda record: record.level.name != "INFO")
    logger._log("LOG", "this shouldn't be printed", stack_level=1)
    io.seek(0)
    assert not io.read()
    logger._log("INFO", "this shouldn't be printed either")
    io.seek(0)
    assert not io.read()

    # test actually  writing
    logger.remove(1)
    logger.add(io, log_format=get_config(lambda record: record.message))
    logger._log("LOG", "message", stack_level=1)
    io.seek(0)
    assert io.read() == "message"


def test_log() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.log("LOG", "test-log")
    io.seek(0)
    assert io.read() == "test-log"


def test_info() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.info("test-info")
    io.seek(0)
    assert io.read() == "test-info"


def test_debug() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.debug("test-debug")
    io.seek(0)
    assert io.read() == "test-debug"


def test_trace() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.trace("test-trace")
    io.seek(0)
    assert io.read() == "test-trace"


def test_success() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.success("test-success")
    io.seek(0)
    assert io.read() == "test-success"


def test_warning() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.warning("test-warning")
    io.seek(0)
    assert io.read() == "test-warning"


def test_error() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.error("test-error")
    io.seek(0)
    assert io.read() == "test-error"


def test_critical() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))
    logger.critical("test-critical")
    io.seek(0)
    assert io.read() == "test-critical"


def test_log_exception() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    try:
        raise ZeroDivisionError
    except ZeroDivisionError as e:
        logger.log_exception(e, "logged-error")

    io.seek(0)
    assert io.read() == "logged-error"


def test_log_func() -> None:
    io, logger = get_stringio_logger(get_config("%{msg}%"))

    @logger.log_func("LOG")
    def dummy(a: int, b: str) -> tuple[str, int]:
        return b, a

    args = 11, "string"
    result = dummy(*args)
    io.seek(0)
    first, second = io.readlines()

    assert dummy.__name__ in first and repr(args) in first
    assert dummy.__name__ in second and repr(result) in second

    io.truncate(0)
    io.seek(0)

    @logger.log_func("LOG")
    async def async_dummy(a: int, b: str) -> tuple[str, int]:
        return b, a

    args = 11, "string"
    result = run(async_dummy(*args))
    io.seek(0)
    first, second = io.readlines()

    assert async_dummy.__name__ in first and repr(args) in first
    assert async_dummy.__name__ in second and repr(result) in second

    io.truncate(0)
    io.seek(0)

    @logger.log_func("LOG")
    def gen_dummy(a: int, b: str) -> Iterator[int | str]:
        yield b
        yield a

    args = 11, "string"
    results = list(gen_dummy(*args))
    io.seek(0)
    first, *yields, last = io.readlines()

    assert gen_dummy.__name__ in first and repr(args) in first
    for res, line in zip(results, yields, strict=True):
        assert gen_dummy.__name__ in line and repr(res) in line
    assert gen_dummy.__name__ in last and "exhausted" in last

    io.truncate(0)
    io.seek(0)

    @logger.log_func("LOG")
    async def async_gen_dummy(a: int, b: str) -> AsyncIterator[int | str]:
        yield b
        yield a

    async def do_async_gen_dummy_test() -> None:
        args = 11, "string"
        results = [e async for e in async_gen_dummy(*args)]
        io.seek(0)
        first, *yields, last = io.readlines()

        assert async_gen_dummy.__name__ in first and repr(args) in first
        for res, line in zip(results, yields, strict=True):
            assert async_gen_dummy.__name__ in line and repr(res) in line
        assert async_gen_dummy.__name__ in last and "exhausted" in last

    run(do_async_gen_dummy_test())


def test_catch_func() -> None:
    # Normal function
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    ## test message
    @logger.catch_func("caught-error")
    def error_caught(a: int, b: int) -> float:
        return a / b

    error_caught(1, 0)
    io.seek(0)
    assert io.read() == "caught-error"

    ## test reraise
    @logger.catch_func(reraise=True)
    def error_reraised(a: int, b: int) -> float:
        return a / b

    with raises(ZeroDivisionError):
        error_reraised(1, 0)

    ## test on_error
    on_error_called = False

    def on_err_callback(_: BaseException) -> None:
        nonlocal on_error_called
        on_error_called = True

    @logger.catch_func(on_error=on_err_callback)
    def on_error(a: int, b: int) -> float:
        return a / b

    on_error(1, 0)
    assert on_error_called

    ## test default
    DEFAULT = object()

    @logger.catch_func(default=DEFAULT)
    def default(a: int, b: int) -> float:
        return a / b

    assert default(1, 0) is DEFAULT


def test_catch_func_async() -> None:
    # Async function
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    ## test message
    @logger.catch_func("caught-error")
    async def async_error_caught(a: int, b: int) -> float:
        return a / b

    run(async_error_caught(1, 0))
    io.seek(0)
    assert io.read() == "caught-error"

    ## test reraise
    @logger.catch_func(reraise=True)
    async def async_error_reraised(a: int, b: int) -> float:
        return a / b

    with raises(ZeroDivisionError):
        run(async_error_reraised(1, 0))

    ## test on_error
    async_on_error_called = False

    def async_on_err_callback(_: BaseException) -> None:
        nonlocal async_on_error_called
        async_on_error_called = True

    @logger.catch_func(on_error=async_on_err_callback)
    async def async_on_error(a: int, b: int) -> float:
        return a / b

    run(async_on_error(1, 0))
    assert async_on_error_called

    ## test default
    DEFAULT = object()

    @logger.catch_func(default=DEFAULT)
    async def async_default(a: int, b: int) -> float:
        return a / b

    assert run(async_default(1, 0)) is DEFAULT


def test_catch_func_generator() -> None:
    # Generator function
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    ## test message
    @logger.catch_func("caught-error")
    def generator_error_caught(a: int, b: int) -> Iterator[float]:
        yield a / b

    with raises(StopIteration):
        next(generator_error_caught(1, 0))
    io.seek(0)
    assert io.read() == "caught-error"

    ## test reraise
    @logger.catch_func(reraise=True)
    def generator_error_reraised(a: int, b: int) -> Iterator[float]:
        yield a / b

    with raises(ZeroDivisionError):
        next(generator_error_reraised(1, 0))

    ## test on_error
    generator_on_error_called = False

    def generator_on_err_callback(_: BaseException) -> None:
        nonlocal generator_on_error_called
        generator_on_error_called = True

    @logger.catch_func(on_error=generator_on_err_callback)
    def generator_on_error(a: int, b: int) -> Iterator[float]:
        yield a / b

    with raises(StopIteration):
        next(generator_on_error(1, 0))
    assert generator_on_error_called


def test_catch_func_async_generator() -> None:
    # Async generator function
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    async def do_async_tests() -> None:
        ## test yields from
        @logger.catch_func()
        async def async_generator_yields_from(a: int, b: int) -> AsyncIterator[float]:
            yield a / b

        assert await anext(async_generator_yields_from(1, 2)) == 1 / 2

        ## test message
        @logger.catch_func("caught-error")
        async def async_generator_error_caught(a: int, b: int) -> AsyncIterator[float]:
            yield a / b

        with raises(StopAsyncIteration):
            await anext(async_generator_error_caught(1, 0))
        io.seek(0)
        assert io.read() == "caught-error"

        ## test reraise
        @logger.catch_func(reraise=True)
        async def async_generator_error_reraised(
            a: int, b: int
        ) -> AsyncIterator[float]:
            yield a / b

        with raises(ZeroDivisionError):
            await anext(async_generator_error_reraised(1, 0))

        ## test on_error
        async_generator_on_error_called = False

        def async_generator_on_err_callback(_: BaseException) -> None:
            nonlocal async_generator_on_error_called
            async_generator_on_error_called = True

        @logger.catch_func(on_error=async_generator_on_err_callback)
        async def async_generator_on_error(a: int, b: int) -> AsyncIterator[float]:
            yield a / b

        with raises(StopAsyncIteration):
            await anext(async_generator_on_error(1, 0))
        assert async_generator_on_error_called

    run(do_async_tests())


def test_catch_context() -> None:
    io, logger = get_stringio_logger(get_config(lambda record: record.message))

    with logger.catch_context("error-caught"):
        _x = 0 / 0

    io.seek(0)
    assert io.read() == "error-caught"

    with raises(ZeroDivisionError):
        with logger.catch_context(reraise=True):
            _x = 0 / 0

    on_error_called = False

    def on_error(_: BaseException) -> None:
        nonlocal on_error_called
        on_error_called = True

    with logger.catch_context(on_error=on_error):
        _x = 0 / 0

    assert on_error_called


def test_add() -> None:
    logger = Logger("TEST")

    sink = DummySink(lambda _: None, None, get_config("%{msg}%"))
    logger.add(sink)

    assert sink in logger._sinks.values()

    # TODO: add proper testing testing for adding files

    logger.add(lambda _: None, min_level="LOG")
    logger.add(lambda _: None, min_level=0)
    logger.add(lambda _: None, min_level=Level("LEVEL", 0))
    sinks = list(logger._sinks.values())

    assert sinks[-3].config.min_level == 0
    assert sinks[-2].config.min_level == 0
    assert sinks[-1].config.min_level == 0

    with raises(LevelDoesNotExistError):
        logger.add(lambda _: None, min_level="does-not-exist")

    cfg = get_config("%{msg}%")
    logger.add(lambda _: None, log_format=cfg)
    cfg_opts = {
        "log_format": "%{msg}%",
        "log_filter": lambda _: True,
        "colourise": False,
        "min_level": 5,
    }
    logger.add(lambda _: None, **cfg_opts)  # type: ignore
    sinks = list(logger._sinks.values())

    assert sinks[-2].config is cfg
    assert (
        sinks[-1].config.formatter == cfg_opts["log_format"]
        and sinks[-1].config.colourise == cfg_opts["colourise"]
        and sinks[-1].config.min_level == cfg_opts["min_level"]
        and sinks[-1].config.filter_func == cfg_opts["log_filter"]
    )


def test_remove() -> None:
    logger = Logger("TEST")

    was_closed = False

    def close() -> None:
        nonlocal was_closed
        was_closed = True

    sink_id = next(logger._sink_id_getter)
    sink = DummySink(lambda _: None, close, get_config("%{msg}%"))
    logger._sinks.update({sink_id: sink})
    logger.remove(sink_id)

    assert sink_id not in logger._sinks
    assert was_closed

    with raises(SinkDoesNotExistError):
        logger.remove(123)


def test_add_level() -> None:
    logger = Logger("TEST")
    level = logger.add_level("TEST-LEVEL", 50, (FgColour.RED,))

    assert level.name == "TEST-LEVEL"
    assert level.severity == 50
    assert level.colours == (FgColour.RED,)
    assert "TEST-LEVEL" in logger._levels


def test_remove_level() -> None:
    logger = Logger("TEST")
    test_level_1 = Level("TEST-LEVEL-1", 50, (FgColour.RED,))
    test_level_2 = Level("TEST-LEVEL-2", 80, (FgColour.BLUE,))
    logger._levels.update({"TEST-LEVEL-1": test_level_1, "TEST-LEVEL-2": test_level_2})
    logger.remove_level(test_level_1.name)
    logger.remove_level(test_level_2)

    assert test_level_1.name not in logger._levels
    assert test_level_2.name not in logger._levels

    with raises(LevelDoesNotExistError):
        logger.remove_level("does-not-exist")


def test_enable() -> None:
    logger = Logger("TEST")
    logger._disabled_for.add("test")
    logger._disabled_for.add(__name__)
    logger.enable("test")
    logger.enable()

    assert "test" not in logger._disabled_for
    assert __name__ not in logger._disabled_for
    # look for exception
    logger.enable("does-not-exist")


def test_disable() -> None:
    logger = Logger("TEST")
    logger.disable("test")
    logger.disable()

    assert "test" in logger._disabled_for
    assert __name__ in logger._disabled_for
