import pytest
from scripts.performance import percentile_nearest_rank


def test_nearest_rank_percentile_uses_recorded_samples() -> None:
    values = [float(value) for value in range(1, 21)]
    assert percentile_nearest_rank(values, 95) == 19


def test_nearest_rank_percentile_handles_one_sample() -> None:
    assert percentile_nearest_rank([12.5], 95) == 12.5


@pytest.mark.parametrize("percentile", [0, -1, 101])
def test_nearest_rank_percentile_rejects_invalid_percentiles(percentile: float) -> None:
    with pytest.raises(ValueError, match="percentile"):
        percentile_nearest_rank([1.0], percentile)


def test_nearest_rank_percentile_requires_samples() -> None:
    with pytest.raises(ValueError, match="sample"):
        percentile_nearest_rank([], 95)
