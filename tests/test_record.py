from datetime import datetime
from multiprocessing import current_process
from sys import _getframe
from threading import current_thread

from pytraced import Level, Record


def test_record_creation() -> None:
    logger_name = "record"
    global_name = "__name__"
    level = Level("level", 0)
    date_time = datetime.now()
    stack_trace = _getframe()
    message = "message"
    process = current_process()
    thread = current_thread()
    extra_info = {"123": 123}

    try:
        raise Exception  # pylint: disable=broad-exception-raised
    except Exception as e:  # pylint: disable=broad-exception-caught
        exception = e

    record = Record(
        logger_name,
        global_name,
        level,
        date_time,
        stack_trace,
        message,
        process,
        thread,
        extra_info,
        exception,  # pylint: disable=used-before-assignment
    )

    assert record.logger_name is logger_name
    assert record.global_name is global_name
    assert record.level is level
    assert record.date_time is date_time
    assert record.frame is stack_trace
    assert record.message is message
    assert record.process is process
    assert record.thread is thread
    assert record.extra_info is extra_info
    assert record.exception is exception
