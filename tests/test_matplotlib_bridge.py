import matplotlib.pyplot as plt

import figworks
from figworks.matplotlib import connect, insert, mpl_to_svg, svg_to_image_artist


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
    mpl_fig, _ = plt.subplots()
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


def test_compose_places_svg_in_axes_without_a_figworks_figure(tmp_path):
    mpl_fig, ax = plt.subplots()
    source = tmp_path / "source.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<circle id="replacement" cx="5" cy="5" r="4"/></svg>',
        encoding="utf-8",
    )

    output = figworks.compose({ax: source}, fig=mpl_fig)

    assert "figworks-compose-0" not in output
    assert 'id="replacement"' in output
    assert 'transform="translate(0 0)"' not in output
    assert not ax.patches


def test_compose_uses_the_current_matplotlib_figure():
    _mpl_fig, ax = plt.subplots()
    source = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><circle/></svg>'

    assert "circle" in figworks.compose({ax: source})


def test_inserting_matplotlib_svg_keeps_ids_unique_and_references_resolved():
    from lxml import etree

    from figworks.core.element import _references

    outer, axes = plt.subplots(1, 2)
    inner, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], marker="o")
    for index, target in enumerate(axes):
        connect(target, f"slot-{index}", 0.1, 0.1, 0.8, 0.8)
    result = insert({"slot-0": inner, "slot-1": inner}, fig=outer)
    root = etree.fromstring(result.encode())
    ids = root.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert _references(root) <= set(ids)
    plt.close(inner)
    plt.close(outer)
