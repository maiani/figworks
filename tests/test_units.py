from figforge.core.units import to_px


def test_to_px_supported_units():
    assert to_px(12) == 12
    assert to_px("12px") == 12
    assert round(to_px("1in"), 6) == 96
    assert round(to_px("25.4mm"), 6) == 96
    assert round(to_px("2.54cm"), 6) == 96
    assert round(to_px("72pt"), 6) == 96
