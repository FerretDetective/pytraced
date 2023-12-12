from datetime import datetime, timezone

from pytraced._datetime import _get_utc_offset, format_datetime


def test_format_datetime() -> None:
    d = datetime.now()

    assert format_datetime(d, "YYYY") == d.strftime("%Y")
    assert format_datetime(d, "YY") == d.strftime("%y")

    assert format_datetime(datetime(2000, 1, 1), "Q") == "1"

    assert format_datetime(d, "MMMM") == d.strftime("%B")
    assert format_datetime(d, "MMM") == d.strftime("%b")
    assert format_datetime(d, "MM") == d.strftime("%m")
    assert format_datetime(d, "M") == str(d.month)

    assert format_datetime(d, "DDDD") == f"{d.timetuple().tm_yday:03}"
    assert format_datetime(d, "DDD") == str(d.timetuple().tm_yday)
    assert format_datetime(d, "DD") == d.strftime("%d")
    assert format_datetime(d, "D") == str(d.day)

    assert format_datetime(d, "ddd") == d.strftime("%A")
    assert format_datetime(d, "dd") == d.strftime("%a")
    assert format_datetime(d, "d") == str(int(d.strftime("%w")) - 1)

    assert format_datetime(d, "A") == "PM" if d.hour >= 12 else "AM"

    assert format_datetime(d, "HH") == d.strftime("%I")
    assert format_datetime(d, "H") == str(((d.hour - 1) % 12) + 1)
    assert format_datetime(d, "hh") == d.strftime("%H")
    assert format_datetime(d, "h") == str(d.hour)

    assert format_datetime(d, "mm") == d.strftime("%M")
    assert format_datetime(d, "m") == str(d.minute)

    assert format_datetime(d, "ss") == d.strftime("%S")
    assert format_datetime(d, "s") == str(d.second)

    assert format_datetime(d, "SSSSSS") == d.strftime("%f")
    assert format_datetime(d, "SSSSS") == d.strftime("%f")[:-1]
    assert format_datetime(d, "SSSS") == d.strftime("%f")[:-2]
    assert format_datetime(d, "SSS") == d.strftime("%f")[:-3]
    assert format_datetime(d, "SS") == d.strftime("%f")[:-4]
    assert format_datetime(d, "S") == d.strftime("%f")[:-5]

    assert format_datetime(d, "Z") == d.astimezone().strftime("%Z")
    assert format_datetime(d, "z") == d.astimezone().strftime("%z")

    assert format_datetime(d, "X") == str(d.timestamp())
    assert format_datetime(d, "x") == str(int((d.timestamp() * 1e6) + d.microsecond))


# Define test cases for _get_utc_offset function
def test_get_utc_offset_with_timezone() -> None:
    date_time = datetime(2023, 9, 26, 12, 0, 0, tzinfo=timezone.utc)
    offset = _get_utc_offset(date_time)
    assert offset == "+0000"


def test_get_utc_offset_without_timezone() -> None:
    date_time = datetime(2023, 9, 26, 12, 0, 0)
    offset = _get_utc_offset(date_time)
    assert offset is None


# Define test cases for format_datetime function
def test_format_datetime_with_valid_format() -> None:
    date_time = datetime(2023, 9, 26, 12, 0, 0)
    formatted_datetime = format_datetime(date_time, "YYYY-MM-DD HH:mm:ss")
    assert formatted_datetime == "2023-09-26 12:00:00"
