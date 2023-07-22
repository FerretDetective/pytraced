from re import Pattern
from re import compile as compile_re

from pytest import raises

from pytraced._config import (
    Config,
    FormatLiteral,
    InvalidFormatSpecifierError,
    TraceStyle,
)


def test_config_constants() -> None:
    assert hasattr(Config, "FORMAT_PARSER") and isinstance(
        Config.FORMAT_PARSER, Pattern
    )
    assert hasattr(Config, "DEFAULT") and isinstance(Config.DEFAULT, str)


def test_format_literal() -> None:
    REG_EXP = compile_re("%{.+?}%")
    for fmt in FormatLiteral:
        assert REG_EXP.fullmatch(fmt.value)


def test_invalid_format_specifier_error() -> None:
    assert issubclass(InvalidFormatSpecifierError, Exception)


def test_config_creation() -> None:
    # test correct attrs
    opts = lambda _: "", None, False, 50
    config = Config(*opts)
    assert config.formatter == opts[0]
    assert config.filter_func == opts[1]
    assert config.colourise == opts[2]
    assert config.min_level == opts[3]
    assert config.date_fmt is None
    assert config.trace_style is None

    # default all format specifiers
    config = Config(
        "[%{name}%][%{lvl}%][%{time:yyyy-mm-dd HH:MM:SS.FS tzo}%]"
        "[%{process-name}%, %{process-id}% : %{thread-name}%, %{thread-id}%]"
        "[%{global-name}%][%{trace:clean}%] - %{msg}%",
        None,
        True,
        0,
    )
    assert (
        config.formatter == f"[{FormatLiteral.NAME.value}][{FormatLiteral.LEVEL.value}]"
        f"[{FormatLiteral.DATE_TIME.value}][{FormatLiteral.PROCESS_NAME.value}, "
        f"{FormatLiteral.PROCESS_ID.value} : {FormatLiteral.THREAD_NAME.value}, "
        f"{FormatLiteral.THREAD_ID.value}][{FormatLiteral.GLOBAL_NAME.value}]"
        f"[{FormatLiteral.TRACE.value}] - {FormatLiteral.MESSAGE.value}"
    )
    assert config.date_fmt == "%Y-%m-%d %H:%M:%S.%f %z"
    assert config.trace_style is TraceStyle.CLEAN

    # test default time
    config = Config("%{time}%", None, False, 0)
    assert config.date_fmt == "%Y-%m-%d %H:%M:%S.%f %z"

    # test default trace style
    config = Config("%{trace}%", None, False, 0)
    assert config.trace_style is TraceStyle.CLEAN

    # test exception raised for invalid trace style
    with raises(InvalidFormatSpecifierError):
        Config("%{trace:does-not-exist}%", None, False, 0)

    # test invalid format specifier
    with raises(InvalidFormatSpecifierError):
        Config("%{does-not-exist}%", None, False, 0)


def test_config_repr() -> None:
    opts = lambda _: "", None, False, 50
    config_repr = repr(Config(*opts))
    for opt in opts:
        assert repr(opt) in config_repr


def test_config_str() -> None:
    opts = lambda _: "", None, False, 50
    config_str = str(Config(*opts))
    assert f"formatter: {opts[0]}" in config_str
    assert f"date_fmt: {None}" in config_str
    assert f"filter_func: {None}" in config_str
    assert f"colourise: {opts[2]}" in config_str
    assert f"min_level: {opts[3]}" in config_str
