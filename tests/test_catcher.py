from typing import Mapping

from pytest import raises

from pytraced import Logger, logger
from pytraced._catcher import Catcher
from pytraced._levels import Level


def test_creation() -> None:
    msg = object()
    catcher = Catcher(False, logger, msg, "LOG", Exception, None, False, None, None)
    assert catcher.from_decorator is False
    assert catcher.logger is logger
    assert catcher.message is msg
    assert catcher.level == "LOG"
    assert catcher.exc_types is Exception
    assert catcher.reraise is False
    assert catcher.on_error is None


def test_repr() -> None:
    opts = False, logger, "message", "LOG", Exception, None, False, None, None
    string = repr(Catcher(*opts))
    for opt in opts:
        assert repr(opt) in string


def test_enter() -> None:
    with Catcher(
        False, logger, "message", "LOG", Exception, None, False, None, None
    ) as c:
        assert c is None


def test_exit() -> None:
    # pylint: disable=unnecessary-dunder-call, broad-exception-raised
    catcher = Catcher(
        False, logger, "message", "LOG", Exception, None, False, None, None
    )

    catcher.__enter__()
    assert catcher.__exit__(None, None, None) is None

    with raises(BaseException):
        with catcher:
            raise BaseException

    logged = None

    class LogPatch(Logger):
        def _log(
            self,
            level: str | Level,
            message: object,
            exception: BaseException | None = None,
            extra_info: Mapping[str, object] | None = None,
            stack_level: int = 2,
        ) -> None:
            nonlocal logged
            logged = message
            return super()._log(level, message, exception, extra_info, stack_level)

    with Catcher(
        False, LogPatch("TEST"), "message", "LOG", Exception, None, False, None, None
    ):
        raise Exception

    assert logged == "message"

    stack_level_ = None

    class LevelPatch(Logger):
        def _log(
            self,
            level: str | Level,
            message: object,
            exception: BaseException | None = None,
            extra_info: Mapping[str, object] | None = None,
            stack_level: int = 2,
        ) -> None:
            nonlocal stack_level_
            stack_level_ = stack_level
            return super()._log(level, message, exception, extra_info, stack_level)

    l = LevelPatch("test")

    with Catcher(True, l, "message", "LOG", Exception, None, False, None, None):
        raise Exception

    assert stack_level_ == 3

    with Catcher(False, l, "message", "LOG", Exception, None, False, None, None):
        raise Exception

    assert stack_level_ == 2

    on_err_called = False

    def on_err(_e: BaseException) -> None:
        nonlocal on_err_called
        on_err_called = True

    with Catcher(False, logger, "message", "LOG", Exception, None, False, on_err, None):
        raise Exception

    assert on_err_called
