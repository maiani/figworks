"""Imported ids stay unique: kept when free, prefixed on collision, shared when identical."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from figworks import Figure
from figworks.core.element import SVG_NS

XLINK = "http://www.w3.org/1999/xlink"


def source(color: str = "red", *, extra: str = "") -> str:
    """A document whose shape references a gradient through every kind of reference."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="{XLINK}" viewBox="0 0 10 10">'
        f'<defs><linearGradient id="g"><stop offset="0" stop-color="{color}"/></linearGradient>'
        '<path id="dot" d="M 0 0 L 1 0"/></defs>'
        '<rect id="box" width="10" height="10" fill="url(#g)" style="stroke: url(\'#g\')"/>'
        '<use href="#dot"/><use xlink:href="#dot"/>'
        f"{extra}</svg>"
    )


def ids(figure: Figure) -> list[str]:
    return [node.get("id") for node in figure.document.root.iter() if node.get("id")]


def node(figure: Figure, id: str):
    found = figure.document.root.find(f".//*[@id='{id}']")
    assert found is not None, id
    return found


def two_panels(first: str, second: str, ids: tuple[str, str] = ("p1", "p2")) -> Figure:
    figure = Figure(width=200, height=100)
    figure.add(first, x=0, y=0, w=100, h=100, id=ids[0])
    figure.add(second, x=100, y=0, w=100, h=100, id=ids[1])
    return figure


def test_ids_that_do_not_collide_are_kept() -> None:
    figure = Figure(width=100, height=100)
    figure.add(source(), x=0, y=0, w=100, h=100, id="p1")
    assert {"g", "dot", "box"} <= set(ids(figure))


def test_colliding_ids_are_prefixed_with_the_placement_id() -> None:
    figure = two_panels(source("red"), source("blue"))
    assert len(ids(figure)) == len(set(ids(figure)))
    assert {"g", "box", "p2-g", "p2-box"} <= set(ids(figure))


def test_every_kind_of_reference_follows_the_rename() -> None:
    figure = two_panels(source("red"), source("blue"))
    box = node(figure, "p2-box")
    assert box.get("fill") == "url(#p2-g)"
    assert box.get("style") == "stroke: url('#p2-g')"
    uses = list(node(figure, "p2").iter(f"{{{SVG_NS}}}use"))
    assert uses[0].get("href") == "#dot" and uses[1].get(f"{{{XLINK}}}href") == "#dot"


def test_each_source_keeps_its_own_definition() -> None:
    figure = two_panels(source("red"), source("blue"))
    stop = f"{{{SVG_NS}}}stop"
    assert node(figure, "g").find(stop).get("stop-color") == "red"
    assert node(figure, "p2-g").find(stop).get("stop-color") == "blue"


def test_identical_definitions_are_shared_not_duplicated() -> None:
    """`dot` is the same in both sources, so the second reuses the first's."""
    figure = two_panels(source("red"), source("blue"))
    assert ids(figure).count("dot") == 1
    assert "p2-dot" not in ids(figure)


def test_identical_matplotlib_panels_share_their_markers() -> None:
    """Matplotlib content-hashes marker and clip-path ids, so equal plots collide."""

    def plot() -> object:
        mpl_fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], marker="o")
        return mpl_fig

    first, second = plot(), plot()
    figure = Figure(width=200, height=100)
    figure.add(first, x=0, y=0, w=100, h=100, id="a")
    figure.add(second, x=100, y=0, w=100, h=100, id="b")
    plt.close("all")
    assert len(ids(figure)) == len(set(ids(figure)))
    clip_paths = figure.document.root.iter(f"{{{SVG_NS}}}clipPath")
    assert len(list(clip_paths)) == 1, "the identical clip path is defined once"


def test_prefix_falls_back_when_the_placement_has_no_id() -> None:
    figure = Figure(width=200, height=100)
    figure.add(source(), x=0, y=0, w=100, h=100)
    figure.add(source("blue"), x=100, y=0, w=100, h=100)
    assert "import2-g" in ids(figure)


def test_a_taken_prefixed_id_gets_a_suffix() -> None:
    figure = two_panels(source("red"), source("blue", extra='<g id="p2-g"/>'))
    assert {"p2-g", "p2-g-2"} <= set(ids(figure))
    assert len(ids(figure)) == len(set(ids(figure)))


def test_a_reused_placement_id_is_rejected() -> None:
    figure = Figure(width=200, height=100)
    figure.add(source(), x=0, y=0, w=100, h=100, id="p1")
    with pytest.raises(ValueError, match="already used"):
        figure.add(source(), x=100, y=0, w=100, h=100, id="p1")


def test_filled_content_is_prefixed_with_the_target_id() -> None:
    figure = Figure(width=200, height=100)
    figure.add(source(), x=0, y=0, w=100, h=100, id="p1")
    figure.document.group(id="slot", transform="translate(150 50)")
    figure.fill_slot(
        "slot", source("blue").replace('viewBox="0 0 10 10"', 'width="10" height="10"')
    )
    assert "slot-g" in ids(figure)
