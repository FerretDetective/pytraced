from io import StringIO
from typing import Callable

from pytraced import Config, Logger, Record, Sink


def get_config(fmt: str | Callable[[Record], str]) -> Config:
    return Config(fmt, None, False, 0)


def get_stringio_logger(log_format: Config) -> tuple[StringIO, Logger]:
    logger = Logger("TEST")
    io = StringIO()
    logger.add(io, log_format=log_format)
    return io, logger


class DummySink(Sink):
    def write(self, string: str) -> None:
        pass
