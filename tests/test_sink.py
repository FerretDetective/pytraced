from datetime import datetime
from io import StringIO
from multiprocessing import current_process
from sys import _getframe
from threading import current_thread

from pytraced import Level, Record
from pytraced._sink import Sink, SinkDoesNotExistError, SyncSink

from .conftest import DummySink, get_config


def test_subclasses() -> None:
    assert issubclass(SyncSink, Sink)


def test_sink_does_not_exist_error() -> None:
    assert issubclass(SinkDoesNotExistError, Exception)


def test_syncsink_creation() -> None:
    opts = lambda _: None, lambda: None, get_config("%{msg}%")
    sink = SyncSink(*opts)
    assert sink.out is opts[0]
    assert sink.close is opts[1]
    assert sink.config is opts[2]


def test_sink_format() -> None:
    assert (
        DummySink(lambda _: None, None, get_config("%{gname}%")).format(
            Record(
                "TEST_LOGGER",
                __name__,
                Level("LEVEL", 0),
                datetime.now(),
                _getframe(),
                "MESSAGE",
                current_process(),
                current_thread(),
                None,
            )
        )
        == f"{__name__}\n"
    )
    assert (
        DummySink(lambda _: None, None, get_config(lambda _: __name__)).format(
            Record(
                "TEST_LOGGER",
                __name__,
                Level("LEVEL", 0),
                datetime.now(),
                _getframe(),
                "MESSAGE",
                current_process(),
                current_thread(),
                None,
            )
        )
        == __name__
    )


def test_syncsink() -> None:
    MESSAGE = "message"

    io = StringIO()
    io_sink = SyncSink(io, None, get_config("%{msg}%"))
    io_sink.write(MESSAGE)
    io.seek(0)
    assert io.read() == MESSAGE

    written = None

    def writer(string: str) -> None:
        nonlocal written
        written = string

    callable_sink = SyncSink(writer, None, get_config("%{msg}%"))
    callable_sink.write(MESSAGE)
    assert written == MESSAGE
