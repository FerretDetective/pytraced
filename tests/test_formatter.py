from datetime import datetime
from multiprocessing import current_process
from os.path import basename
from pathlib import Path
from sys import _getframe
from threading import current_thread
from traceback import extract_stack, format_exception, format_list

from pytraced import Config, Level, Record
from pytraced._config import TraceStyle
from pytraced._formatter import _format, _format_date_time, _format_path, format_record
from pytraced.colours import FgColour, add_colours


def test_format_date_time() -> None:
    date_time = datetime.now().astimezone()

    # test %f changes
    f_time = date_time.strftime("%f")[:-3]
    assert _format_date_time(date_time, "%f.%f") == f"{f_time}.{f_time}"

    # test remaining strftime directives
    # fmt: off
    for e in (
        "%a", "%A", "%b", "%B", "%c", "%d", "%H", "%I", "%j", "%m", "%M",
        "%p", "%S", "%U", "%w", "%W", "%x", "%X", "%y", "%Y", "%z", "%Z",
    ):
        assert _format_date_time(date_time, e) == date_time.strftime(e)


def test_format_path() -> None:
    assert _format_path("<stdin>") == "<stdin>"

    path = Path.cwd() / "some-directory" / "test-file.py"
    assert _format_path(str(path)) == str(path.relative_to(Path.cwd()))


def test_format() -> None:
    logger_name = "record"
    global_name = "__name__"
    level = Level("level", 0)
    date_time = datetime.now().astimezone()
    frame = _getframe(1)
    message = "message"
    process = current_process()
    thread = current_thread()

    try:
        raise Exception  # pylint: disable=broad-exception-raised
    except Exception as e:  # pylint: disable=broad-exception-caught
        exception = e

    record = Record(
        logger_name,
        global_name,
        level,
        date_time,
        frame,
        message,
        process,
        thread,
        exception,  # pylint: disable=used-before-assignment
    )
    config = Config("", None, False, 0)

    assert _format("%{name}%", record, config) == logger_name
    assert _format("%{lvl}%", record, config) == level.name
    assert _format("%{gname}%", record, config) == global_name
    assert _format("%{pname}%", record, config) == process.name
    assert _format("%{pid}%", record, config) == str(process.ident)
    assert _format("%{tname}%", record, config) == thread.name
    assert _format("%{tid}%", record, config) == str(thread.ident)
    assert _format("%{msg}%", record, config) == message

    config.date_fmt = "%c %Z %z"
    assert _format("%{date_time}%", record, config) == date_time.strftime(
        config.date_fmt
    )

    config.trace_style = TraceStyle.BARE
    assert _format("%{trace}%", record, config) == (
        f"{basename(frame.f_code.co_filename)}:{frame.f_lineno}"
    )
    config.trace_style = TraceStyle.SIMPLE
    assert _format("%{trace}%", record, config) == (
        f"{global_name}@{frame.f_code.co_name}:{frame.f_lineno}"
    )
    config.trace_style = TraceStyle.CLEAN
    assert _format("%{trace}%", record, config) == (
        f"{_format_path(frame.f_code.co_filename)}@"
        f"{frame.f_code.co_name}:{frame.f_lineno}"
    )
    config.trace_style = TraceStyle.DETAILED
    assert _format("%{trace}%", record, config) == " -> ".join(
        f"{_format_path(trace.filename)}@{trace.name}:{trace.lineno}"
        for trace in extract_stack(record.frame)
    )
    config.trace_style = TraceStyle.FULL
    assert _format("%{trace}%", record, config) == "\n{}\n".format(
        "\n".join(format_list(extract_stack(record.frame)))
    )

    # test for infinite recursion
    assert (
        _format(
            "%{msg}%",
            Record(
                logger_name,
                global_name,
                level,
                date_time,
                frame,
                "%{msg}%",
                process,
                thread,
                exception,  # pylint: disable=used-before-assignment
            ),
            config,
        )
        == "%{msg}%"
    )


def test_format_record() -> None:
    logger_name = "record"
    global_name = "__name__"
    level = Level("level", 0)
    date_time = datetime.now()
    frame = _getframe(1)
    message = "message"
    process = current_process()
    thread = current_thread()

    try:
        raise Exception  # pylint: disable=broad-exception-raised
    except Exception as e:  # pylint: disable=broad-exception-caught
        exception = e

    # test formatting exceptions
    assert format_record(
        Record(
            logger_name,
            global_name,
            level,
            date_time,
            frame,
            message,
            process,
            thread,
            exception,  # pylint: disable=used-before-assignment
        ),
        Config("", None, False, 0),
    ) == "".join(format_exception(exception))
    assert (
        format_record(
            Record(
                logger_name,
                global_name,
                level,
                date_time,
                frame,
                message,
                process,
                thread,
                exception,  # pylint: disable=used-before-assignment
            ),
            Config("TEST", None, False, 0),
        )
        == f"TEST\n{''.join(format_exception(exception))}"
    )
    assert (
        format_record(
            Record(
                logger_name,
                global_name,
                level,
                date_time,
                frame,
                message,
                process,
                thread,
                None,
            ),
            Config("", None, False, 0),
        )
        == "\n"
    )

    # test colourizing
    assert (
        format_record(
            Record(
                logger_name,
                global_name,
                Level("level", 0, [FgColour.BLACK]),
                date_time,
                frame,
                message,
                process,
                thread,
                None,
            ),
            Config("TEST", None, False, 0),
        )
        == "TEST\n"
    )
    assert format_record(
        Record(
            logger_name,
            global_name,
            Level("level", 0, [FgColour.BLACK]),
            date_time,
            frame,
            message,
            process,
            thread,
            None,
        ),
        Config("TEST", None, True, 0),
    ) == add_colours("TEST\n", FgColour.BLACK)
