import matplotlib.pyplot as plt

from figforge.backends.matplotlib import connect, insert, mpl_to_svg, svg_to_image_artist


def test_insert_replaces_placeholder_by_id():
    mpl_fig, ax = plt.subplots()
    connect(ax, "slot", 0.2, 0.2, 0.6, 0.6)

    panel_fig, panel_ax = plt.subplots()
    panel_ax.plot([0, 1], [0, 1])
    panel_ax.set_title("injected")
    panel_svg = mpl_to_svg(panel_fig)

    out = insert({"slot": panel_svg}, fig=mpl_fig)
    assert "injected" in out
    assert 'id="slot"' not in out


def test_insert_raises_for_unknown_id():
    mpl_fig, ax = plt.subplots()
    import pytest

    with pytest.raises(UserWarning):
        insert({"nope": "<svg xmlns='http://www.w3.org/2000/svg'/>"}, fig=mpl_fig)


def test_svg_to_image_artist_returns_offset_image():
    artist = svg_to_image_artist(
        "<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'/>",
        gid="box",
    )
    from matplotlib.offsetbox import OffsetImage

    assert isinstance(artist, OffsetImage)
