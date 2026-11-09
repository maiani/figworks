import pytest

from figworks import Figure
from figworks.core.units import to_px


def test_to_px_supported_units():
    assert to_px(12) == 12
    assert to_px("12px") == 12
    assert round(to_px("1in"), 6) == 96
    assert round(to_px("25.4mm"), 6) == 96
    assert round(to_px("2.54cm"), 6) == 96
    assert round(to_px("72pt"), 6) == 96


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan"), "9" * 400 + "in"])
def test_nonfinite_lengths_are_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        to_px(value)


@pytest.mark.parametrize("value", [0, -1, "0mm", "-2in", float("nan"), float("inf")])
def test_invalid_canvas_dimensions_are_rejected(value):
    with pytest.raises(ValueError):
        Figure(value, 10)
    with pytest.raises(ValueError):
        Figure(10, value)
