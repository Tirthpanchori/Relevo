import pytest
from pydantic import ValidationError

from relevo.api.schemas import TaskError
from relevo.config import Settings
from relevo.engine.retries import retry_delay_seconds


@pytest.mark.parametrize("attempt,low,high", [(1, 0.5, 1), (2, 1, 2), (6, 15, 30), (100, 15, 30)])
def test_equal_jitter_is_positive_exponential_and_capped(
    unit_settings: Settings,
    attempt: int,
    low: float,
    high: float,
) -> None:
    assert retry_delay_seconds(attempt, unit_settings, random_source=lambda: 0) == low
    assert retry_delay_seconds(attempt, unit_settings, random_source=lambda: 1) == high


@pytest.mark.parametrize("sample", [-0.1, 1.1, float("nan")])
def test_invalid_jitter_sample_fails(unit_settings: Settings, sample: float) -> None:
    with pytest.raises(ValueError, match="jitter sample"):
        retry_delay_seconds(1, unit_settings, random_source=lambda: sample)


def test_retry_settings_validate_order(unit_settings: Settings) -> None:
    with pytest.raises(ValidationError, match="retry base"):
        Settings(**{**unit_settings.model_dump(), "retry_base_seconds": 100})


def test_nonpositive_attempt_is_rejected(unit_settings: Settings) -> None:
    with pytest.raises(ValueError, match="positive"):
        retry_delay_seconds(0, unit_settings)


@pytest.mark.parametrize("message", ["bad\x00message", "\ud800"])
def test_error_messages_must_be_storable_json(message: str) -> None:
    with pytest.raises(ValidationError):
        TaskError(code="handler_error", message=message)
