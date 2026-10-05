"""Placing Matplotlib plots by their axes frame, so frames line up across panels."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator

import matplotlib.pyplot as plt
import numpy as np
import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import SVG_NS, accumulated_scale

MM = 96 / 25.4


@pytest.fixture(autouse=True)
def close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def frame_box(
    figure: Figure, gid: str, ctm: Callable[[etree._Element], np.ndarray]
) -> tuple[float, float, float, float]:
    """Document-px (left, top, right, bottom) of an axes background drawn with ``gid``."""
    group = figure.document.root.find(f".//*[@id='{gid}']")
    assert group is not None, gid
    path = group.find(f"{{{SVG_NS}}}path")
    numbers = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))]
    xs, ys = numbers[0::2], numbers[1::2]
    m = ctm(path)
    (x0, y0, _), (x1, y1, _) = m @ [min(xs), min(ys), 1], m @ [max(xs), max(ys), 1]
    return x0, y0, x1, y1


def plot(ax: plt.Axes, gid: str, *, wide_labels: bool = False) -> None:
    ax.patch.set_gid(gid)
    ax.plot([0, 1], [0, 123456 if wide_labels else 1])
    if wide_labels:  # six-digit tick labels, written out in full
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.set_ylabel("y")


def test_subplots_figure_is_the_panel_with_axes_edge_to_edge() -> None:
    figure = Figure(width="100mm", height="60mm")
    panel = figure.panel("a", x="20mm", y="5mm", w="70mm", h="50mm")
    mpl_fig, ax = panel.subplots()
    assert tuple(mpl_fig.get_size_inches()) == pytest.approx((70 / 25.4, 50 / 25.4))
    assert tuple(ax.get_position().bounds) == pytest.approx((0, 0, 1, 1))


def test_a_panel_subplots_figure_is_placed_at_one_to_one(ctm) -> None:
    figure = Figure(width="100mm", height="60mm")
    panel = figure.panel("a", x="20mm", y="5mm", w="70mm", h="50mm")
    mpl_fig, ax = panel.subplots()
    plot(ax, "frame-a")
    group = panel.add(mpl_fig, id="plot-a", fit="axes")

    # Transforms are written to six significant figures.
    assert accumulated_scale(group) == pytest.approx(96 / 72, rel=1e-5), "1 pt is 4/3 px"
    assert frame_box(figure, "frame-a", ctm) == pytest.approx(
        (panel.x, panel.y, panel.x + panel.w, panel.y + panel.h), abs=0.01
    )


def test_text_keeps_its_nominal_size(ctm) -> None:
    figure = Figure(width="100mm", height="60mm")
    panel = figure.panel("a", x="20mm", y="5mm", w="70mm", h="50mm")
    with plt.rc_context({"font.size": 8}):
        mpl_fig, ax = panel.subplots()
        ax.plot([0, 1], [0, 1])
        panel.add(mpl_fig, id="plot-a", fit="axes")
    text = next(figure.document.root.iter(f"{{{SVG_NS}}}text"))
    size = float(re.search(r"font-size: ([\d.]+)px", text.get("style")).group(1))
    assert size * accumulated_scale(text) == pytest.approx(8 * 96 / 72, rel=1e-5)


def test_frames_in_a_row_line_up_whatever_their_labels(ctm) -> None:
    """The reason for fit='axes': fitting content misaligns frames with wider labels."""

    def row(fit: str) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Each frame relative to its own panel's top-left corner."""
        figure = Figure(width="160mm", height="60mm")
        boxes = []
        for name, x, wide in (("a", "20mm", False), ("b", "100mm", True)):
            panel = figure.panel(name, x=x, y="5mm", w="50mm", h="40mm")
            mpl_fig, ax = panel.subplots()
            plot(ax, f"frame-{name}", wide_labels=wide)
            panel.add(mpl_fig, id=f"plot-{name}", fit=fit)  # type: ignore[arg-type]
            left, top, right, bottom = frame_box(figure, f"frame-{name}", ctm)
            boxes.append((left - panel.x, top - panel.y, right - panel.x, bottom - panel.y))
        return boxes[0], boxes[1]

    a, b = row("axes")
    assert a == pytest.approx(b, abs=0.01), "both frames sit exactly on their panels"
    assert a == pytest.approx((0, 0, 50 * MM, 40 * MM), abs=0.01)

    a, b = row("content")
    assert b[0] - a[0] > 1, "fitting content pushes the frame with wider labels further in"


def test_an_ordinary_figure_has_its_frame_fitted_into_the_box(ctm) -> None:
    figure = Figure(width="100mm", height="60mm")
    mpl_fig, ax = plt.subplots(figsize=(3, 2), layout="constrained")
    plot(ax, "frame")
    figure.add(mpl_fig, x="10mm", y="10mm", w="80mm", h="40mm", fit="axes")
    left, top, right, bottom = frame_box(figure, "frame", ctm)
    assert left >= 10 * MM - 0.01 and right <= 90 * MM + 0.01
    assert top >= 10 * MM - 0.01 and bottom <= 50 * MM + 0.01
    assert right - left == pytest.approx(80 * MM, abs=0.01) or bottom - top == pytest.approx(
        40 * MM, abs=0.01
    ), "the fit touches the box on one axis"


def test_the_frame_spans_every_axes(ctm) -> None:
    figure = Figure(width="160mm", height="60mm")
    panel = figure.panel("a", x="15mm", y="5mm", w="130mm", h="45mm")
    mpl_fig, (left_ax, right_ax) = panel.subplots(1, 2, gridspec_kw={"wspace": 0.3})
    plot(left_ax, "frame-left")
    plot(right_ax, "frame-right")
    panel.add(mpl_fig, id="pair", fit="axes")
    assert frame_box(figure, "frame-left", ctm)[0] == pytest.approx(panel.x, abs=0.01)
    assert frame_box(figure, "frame-right", ctm)[2] == pytest.approx(panel.x + panel.w, abs=0.01)


def test_fit_axes_needs_a_matplotlib_figure_with_axes() -> None:
    figure = Figure(width="100mm", height="60mm")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>'
    with pytest.raises(ValueError, match="Matplotlib figure"):
        figure.add(svg, x=0, y=0, w=10, h=10, fit="axes")
    with pytest.raises(ValueError, match="no visible axes"):
        figure.add(plt.figure(), x=0, y=0, w=10, h=10, fit="axes")
    with pytest.raises(ValueError, match="fit must be"):
        figure.add(svg, x=0, y=0, w=10, h=10, fit="frame")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [{"figsize": (3, 2)}, {"layout": "constrained"}, {"gridspec_kw": {"left": 0.1}}],
)
def test_subplots_refuses_what_would_move_the_frame(kwargs: dict[str, object]) -> None:
    panel = Figure(width="100mm", height="60mm").panel("a", x=0, y=0, w="50mm", h="40mm")
    with pytest.raises(ValueError, match="panel sets"):
        panel.subplots(**kwargs)
