"""stats.wilson against statsmodels (S2 E7). statsmodels is a test-only dependency (experiment extra); without it
this file fails to import on purpose, so the only check on wilson cannot vanish as a skip."""
import math

import pytest
from statsmodels.stats import proportion

from jigsaw.experiment.stats import wilson


def alpha_of(z):
    """Two-sided alpha whose critical value is z, so statsmodels uses the same z as wilson."""
    return math.erfc(z / math.sqrt(2))


GRID = [(k, n) for n in (1, 2, 3, 5, 10, 17, 50, 300, 1000, 20000) for k in sorted({0, 1, n // 3, n // 2, n - 1, n})]


@pytest.mark.parametrize("k,n", GRID)
def test_wilson_matches_statsmodels(k, n):
    lo, hi = wilson(k, n)
    elo, ehi = proportion.proportion_confint(k, n, alpha=alpha_of(1.96), method="wilson")
    assert lo == pytest.approx(elo, abs=1e-9) and hi == pytest.approx(ehi, abs=1e-9)


@pytest.mark.parametrize("z", [1.6448536269514722, 2.5758293035489004])
def test_wilson_other_levels(z):
    for k, n in [(0, 40), (3, 40), (40, 40)]:
        lo, hi = wilson(k, n, z=z)
        elo, ehi = proportion.proportion_confint(k, n, alpha=alpha_of(z), method="wilson")
        assert lo == pytest.approx(elo, abs=1e-9) and hi == pytest.approx(ehi, abs=1e-9)


def test_wilson_bounds_and_types():
    lo, hi = wilson(0, 300)
    assert lo == 0.0 and 0 < hi < 0.02 and isinstance(lo, float) and isinstance(hi, float)
    assert wilson(300, 300)[1] == 1.0


def test_wilson_rejects_bad_counts():
    for k, n in [(0, 0), (-1, 5), (6, 5)]:
        with pytest.raises(ValueError):
            wilson(k, n)
