from statistics import mean
from time import perf_counter
from typing import Iterator

from pympler.asizeof import asizeof  # type: ignore

import pytraced


def test_speed() -> None:
    logger = pytraced.Logger("TEST")
    logger.add(lambda _: None)
    num_trials = 1_000

    def do_trials() -> Iterator[float]:
        for _ in range(num_trials):
            start = perf_counter()
            logger.info("msg")
            yield perf_counter() - start

    assert mean(do_trials()) < 1e-4


def test_size() -> None:
    assert asizeof(pytraced.logger) < 15_000
