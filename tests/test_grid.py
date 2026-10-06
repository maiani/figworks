"""Named grids preserve physical gutters, spans, and ordinary panel behavior."""

import matplotlib.pyplot as plt
import pytest

from figworks import Figure, Panel
from figworks.core.element import accumulated_scale
from figworks.core.units import to_px


def box(panel):
    return panel.x, panel.y, panel.w, panel.h


def test_weighted_tracks_and_span_include_internal_gap():
    figure = Figure(120, 100)
    panels = figure.grid(
        [["device", "device"], ["left", "right"]],
        width_ratios=(2, 1),
        height_ratios=(1, 2),
        margins=(5, 7, 9, 11),
        gap=(8, 12),
    )
    # Width: 120 - 11 - 7 - 12 = 90. Height: 100 - 5 - 9 - 8 = 78.
    assert box(panels["device"]) == pytest.approx((11, 5, 102, 26))
    assert box(panels["left"]) == pytest.approx((11, 39, 60, 52))
    assert box(panels["right"]) == pytest.approx((83, 39, 30, 52))
    assert list(panels) == ["device", "left", "right"]
    assert all(
        isinstance(panel, Panel) and figure.panels[name] is panel for name, panel in panels.items()
    )


def test_vertical_span_and_empty_cells():
    panels = Figure(100, 100).grid([["tall", "top", None], ["tall", None, "bottom"]], gap=10)
    assert box(panels["tall"]) == pytest.approx((0, 0, 80 / 3, 100))
    assert box(panels["top"]) == pytest.approx((110 / 3, 0, 80 / 3, 45))
    assert box(panels["bottom"]) == pytest.approx((220 / 3, 55, 80 / 3, 45))


def test_mixed_units_and_single_track():
    panel = Figure("2in", "72pt").grid(
        [["main"]], margins=("1pt", "2mm", "0.1in", "0.2cm"), gap="10mm"
    )["main"]
    assert box(panel) == pytest.approx(
        (to_px("2mm"), 96 / 72, 192 - 2 * to_px("2mm"), 96 - 96 / 72 - 9.6)
    )


def test_resize_preserves_physical_spacing_and_track_ratios():
    layout = [["left", "right"]]
    small = Figure("90mm", "60mm").grid(layout, width_ratios=(2, 1), margins="5mm", gap="8mm")
    large = Figure("180mm", "60mm").grid(layout, width_ratios=(2, 1), margins="5mm", gap="8mm")
    for panels, width in ((small, 90), (large, 180)):
        left, right = panels["left"], panels["right"]
        assert left.x == pytest.approx(to_px("5mm"))
        assert right.x - left.ne.x == pytest.approx(to_px("8mm"))
        assert left.w / right.w == pytest.approx(2)
        assert right.ne.x == pytest.approx(to_px(f"{width - 5}mm"))
    assert small["left"].h == large["left"].h


def test_provider_placement_anchors_and_deterministic_svg():
    class Source:
        def to_svg_document(self):
            return (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                '<rect id="shape" width="10" height="10"/></svg>'
            )

    def build():
        figure = Figure(200, 100)
        panels = figure.grid([["left", "right"]], margins=10, gap=20)
        panels["left"].add(Source(), id="left")
        panels["right"].add(Source(), id="right")
        figure.label("a", panels["left"].nw, id="label-a", dx=0, dy=0)
        panels["right"].text("caption", 1, 2, id="caption")
        assert len(figure.select("#left")) == len(figure.select("#right")) == 1
        assert len(figure.select("#shape")) == len(figure.select("#right-shape")) == 1
        label = next(iter(figure.select("#label-a")))
        assert (label.get("x"), label.get("y")) == ("10", "10")
        caption = next(iter(figure.select("#caption")))
        assert (caption.get("x"), caption.get("y")) == ("111", "12")
        return figure.document.to_string()

    assert build() == build()


def test_grid_panels_keep_matplotlib_at_nominal_size():
    panel = Figure("120mm", "60mm").grid([["plot"]], margins="10mm")["plot"]
    mpl, ax = panel.subplots()
    try:
        ax.plot([0, 1], [0, 1])
        assert mpl.get_size_inches() == pytest.approx((100 / 25.4, 40 / 25.4))
        placed = panel.add(mpl, id="plot", fit="axes")
        assert accumulated_scale(placed) == pytest.approx(96 / 72, rel=1e-5)
    finally:
        plt.close(mpl)


@pytest.mark.parametrize(
    ("layout", "message"),
    [
        ([], "non-empty"),
        ([[]], "non-empty"),
        (["ab"], "sequence of panel IDs"),
        ([["a"], ["b", "c"]], "same length"),
        ([[None]], "at least one panel"),
        ([[""]], "non-empty strings"),
        ([[False]], "non-empty strings"),
        ([["a", "a"], ["a", "b"]], "filled rectangle"),
        ([["a", None, "a"]], "filled rectangle"),
        ([["a", "b"], ["b", "a"]], "filled rectangle"),
    ],
)
def test_invalid_layout_does_not_create_panels(layout, message):
    figure = Figure(100, 100)
    existing = figure.panel("existing", 0, 0, 1, 1)
    with pytest.raises(ValueError, match=message):
        figure.grid(layout)
    assert figure.panels == {"existing": existing}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"width_ratios": (1,)}, "2 entries"),
        ({"height_ratios": ()}, "1 entries"),
        ({"width_ratios": (1, 0)}, "positive numbers"),
        ({"width_ratios": (1, -1)}, "positive numbers"),
        ({"width_ratios": (1, float("inf"))}, "positive numbers"),
        ({"height_ratios": (float("nan"),)}, "positive numbers"),
        ({"width_ratios": (True, 1)}, "positive numbers"),
        ({"width_ratios": ("1", 1)}, "positive numbers"),
        ({"width_ratios": (1e-300, 1e300)}, "too extreme"),
        ({"width_ratios": (1, 1e-30)}, "too extreme"),
        ({"margins": -1}, "non-negative"),
        ({"gap": float("inf")}, "non-negative"),
        ({"margins": (1, 2)}, "top, right, bottom, left"),
        ({"gap": (1, 2, 3)}, "row_gap, column_gap"),
        ({"margins": 50}, "no room"),
        ({"gap": 100}, "no room"),
    ],
)
def test_invalid_geometry_does_not_create_panels(kwargs, message):
    figure = Figure(100, 100)
    with pytest.raises(ValueError, match=message):
        figure.grid([["a", "b"]], **kwargs)
    assert figure.panels == {}


def test_existing_id_collision_is_atomic():
    figure = Figure(100, 100)
    existing = figure.panel("taken", 0, 0, 10, 10)
    with pytest.raises(ValueError, match="Panel already exists: 'taken'"):
        figure.grid([["new", "taken"]])
    assert figure.panels == {"taken": existing}


def test_large_ratios_do_not_overflow():
    panels = Figure(100, 50).grid([["left", "right"]], width_ratios=(1e308, 1e308))
    assert box(panels["left"]) == pytest.approx((0, 0, 50, 50))
    assert box(panels["right"]) == pytest.approx((50, 0, 50, 50))


@pytest.mark.parametrize("width", [0, -10, float("inf"), float("nan")])
def test_grid_rejects_invalid_canvas_dimensions(width):
    figure = Figure(width, 50)
    with pytest.raises(ValueError, match="positive figure dimensions"):
        figure.grid([["main"]])
    assert figure.panels == {}
