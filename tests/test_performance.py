from statistics import mean
from time import perf_counter

from pympler.asizeof import asizeof  # type: ignore

import pytraced


def test_speed() -> None:
    logger = pytraced.Logger("TEST")
    num_trials = 1_000
    times: list[float] = []

    for _ in range(num_trials):
        start = perf_counter()
        logger.info("msg")
        times.append(perf_counter() - start)

    assert mean(times) < 7e-4


def test_size() -> None:
    assert asizeof(pytraced.logger) < 18_000
