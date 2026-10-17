"""Bounded exponential backoff; equal jitter keeps every retry strictly delayed."""

import random
from collections.abc import Callable

from relevo.config import Settings


def retry_delay_seconds(
    attempt_number: int,
    settings: Settings,
    *,
    random_source: Callable[[], float] = random.random,
) -> float:
    if attempt_number < 1:
        raise ValueError("attempt number must be positive")
    ceiling = min(
        settings.retry_max_seconds, settings.retry_base_seconds * 2 ** (attempt_number - 1)
    )
    sample = random_source()
    if not 0 <= sample <= 1:
        raise ValueError("jitter sample must be between zero and one")
    return ceiling / 2 + sample * ceiling / 2
