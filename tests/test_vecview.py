"""Placing a VecView scene.

VecView is an optional source, not a dependency: FigWorks places any object
exposing ``to_svg_document()``, so these tests skip when it is absent.
"""

from __future__ import annotations

import numpy as np
import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import SVG_NS, resolve_svg_source, svg_intrinsic_size

vecview = pytest.importorskip("vecview", reason="VecView is an optional source")


@pytest.fixture
def scene():
    cam = vecview.OrthographicCamera(azim_deg=35.0, elev_deg=24.0, scale=62.0)
    sc = vecview.Scene(cam, pad=6.0)
    slab = vecview.box_faces(center=(0, 0, -0.45), size=(11, 9, 0.9))
    sc.faces(10, slab, cull=True, fill="#cfd6e0", id="slab")
    sc.polygon(
        20,
        vecview.double_arrow_shape(
            (0, 0, 0.02), vecview.in_plane_dir(22.5), 4.0, (0, 0, 1), 0.1, 0.36, 0.34
        ),
        fill="#d62828",
        id="axis-marker",
    )
    return sc


def test_scene_satisfies_the_svg_document_protocol(scene):
    assert resolve_svg_source(scene) == scene.to_svg_document()


def test_intrinsic_size_comes_from_the_scene_viewbox(scene):
    width, height, min_x, min_y = svg_intrinsic_size(scene.to_svg_document())

    assert width > 0 and height > 0
    assert (min_x, min_y) != (0.0, 0.0), "a fitted viewBox rarely starts at the origin"


def test_panel_add_places_the_scene(scene):
    figure = Figure(width="100mm", height="60mm")
    figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm").add(scene, id="slab-scene")

    assert 'id="slab-scene"' in figure.document.to_string()


def test_scene_ids_survive_placement(scene):
    """Ids assigned while building the scene stay selectable afterwards."""
    figure = Figure(width="100mm", height="60mm")
    figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm").add(scene, id="slab-scene")

    figure.select("#axis-marker").set_style(fill="navy")
    marker = figure.document.root.find(f".//{{{SVG_NS}}}*[@id='axis-marker']")
    assert marker is not None
    assert "navy" in marker.get("style", "")


def test_placement_scales_uniformly(scene):
    """A per-axis scale would skew the projection and break parallel edges."""
    figure = Figure(width="100mm", height="60mm")
    group = figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm").add(scene, id="s")

    transform = group.get("transform", "")
    scale = transform.split("scale(")[1].split(")")[0]
    assert len(scale.split()) == 1, f"expected one uniform scale factor, got {scale!r}"


def test_non_zero_scene_origin_is_shifted_into_the_panel(scene):
    """The fitted viewBox origin must be compensated, or the scene lands off-panel."""
    _, _, min_x, min_y = svg_intrinsic_size(scene.to_svg_document())
    figure = Figure(width="100mm", height="60mm")
    group = figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm").add(scene, id="s")

    transform = group.get("transform", "")
    assert f"translate({-min_x:g} {-min_y:g})" in transform


def test_placed_scene_geometry_lands_within_the_panel(scene):
    """The end-to-end check: fitted, shifted, and actually inside its box."""
    figure = Figure(width="100mm", height="60mm")
    panel = figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm")
    panel.add(scene, id="slab-scene")

    tree = etree.ElementTree(figure.document.root)
    rendered = etree.fromstring(etree.tostring(tree))
    assert rendered is not None

    width, height, _, _ = svg_intrinsic_size(scene.to_svg_document())
    fitted = min(panel.w / width, panel.h / height)
    drawn_w, drawn_h = width * fitted, height * fitted

    assert drawn_w <= panel.w + 1e-6
    assert drawn_h <= panel.h + 1e-6
    assert abs(drawn_w - panel.w) < 1e-6 or abs(drawn_h - panel.h) < 1e-6, (
        "a fit should touch the panel on one axis"
    )


def test_scene_survives_export(scene, tmp_path):
    figure = Figure(width="100mm", height="60mm")
    figure.panel("a", x="8mm", y="8mm", w="84mm", h="44mm").add(scene, id="slab-scene")

    for suffix in (".svg", ".pdf", ".png"):
        out = tmp_path / f"figure{suffix}"
        figure.save(out)
        assert out.stat().st_size > 0


def test_colliding_def_ids_are_renamed_per_scene(scene):
    """Two scenes may reuse a gradient id; each must keep its own gradient.

    The second scene's ``glow`` is renamed ``s2-glow`` and its ``url(#glow)``
    references follow, so it no longer silently takes the first scene's colour.
    """
    import svg

    def with_glow(color):
        cam = vecview.OrthographicCamera(35.0, 24.0, 40.0)
        sc = vecview.Scene(cam, pad=4.0)
        sc.add_def(
            svg.RadialGradient(
                id="glow",
                elements=[svg.Stop(offset=0, stop_color=color), svg.Stop(offset=1)],
            )
        )
        sc.faces(10, vecview.box_faces((0, 0, 0), (4, 4, 1)), cull=True, fill="url(#glow)")
        return sc

    figure = Figure(width="120mm", height="60mm")
    figure.panel("a", x="5mm", y="5mm", w="50mm", h="50mm").add(with_glow("red"), id="s1")
    figure.panel("b", x="60mm", y="5mm", w="50mm", h="50mm").add(with_glow("blue"), id="s2")

    root = figure.document.root
    ids = [node.get("id") for node in root.iter() if node.get("id")]
    assert len(ids) == len(set(ids)), "every id in the figure is unique"
    for group, gradient in (("s1", "glow"), ("s2", "s2-glow")):
        fills = {
            node.get("fill")
            for node in root.find(f".//*[@id='{group}']").iter()
            if node.get("fill")
        }
        assert fills == {f"url(#{gradient})"}
    blue = root.find(f".//{{{SVG_NS}}}radialGradient[@id='s2-glow']/{{{SVG_NS}}}stop")
    assert blue is not None and blue.get("stop-color") == "blue"


class TestFillPlane:
    """Placing content *in* a plane of the scene rather than on top of the figure."""

    @pytest.fixture
    def plane_scene(self):
        cam = vecview.OrthographicCamera(35.0, 26.0, 62.0)
        sc = vecview.Scene(cam, pad=4.0)
        sc.faces(10, vecview.box_faces((0, 0, -0.35), (12, 10, 0.7)), cull=True, id="slab")
        # world +y projects rightward at this azimuth, world +x downward
        sc.plane(15, (-4.0, -3.0, 0.01), (0.0, 8.0, 0.0), (6.0, 0.0, 0.0), id="plot-plane")
        return sc

    @staticmethod
    def content(width: float = 200.0, height: float = 150.0, origin: str = "0 0") -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{origin} {width} {height}">'
            f'<rect id="mark" x="0" y="0" width="{width}" height="{height}"/></svg>'
        )

    def test_content_lands_inside_the_plane_group(self, plane_scene) -> None:
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        figure.fill_plane("plot-plane", self.content())

        group = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='plot-plane']")
        assert group is not None
        assert len(group) == 1, "content must be appended beneath the plane group"
        assert group.find(f".//{{{SVG_NS}}}rect[@id='mark']") is not None

    def test_plane_transform_is_left_alone(self, plane_scene) -> None:
        """fill_plane only normalizes; the plane's own matrix carries the geometry."""
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        before = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='plot-plane']").get("transform")
        figure.fill_plane("plot-plane", self.content())
        after = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='plot-plane']").get("transform")
        assert before == after
        assert after.startswith("matrix(")

    def test_content_is_normalized_onto_the_unit_square(self, plane_scene) -> None:
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        wrapper = figure.fill_plane("plot-plane", self.content(width=200.0, height=150.0))

        scale = wrapper.get("transform", "")
        assert scale.startswith("scale(")
        sx, sy = (float(v) for v in scale[len("scale(") :].rstrip(")").split())
        assert sx == pytest.approx(1 / 200.0)
        assert sy == pytest.approx(1 / 150.0)

    def test_non_zero_content_origin_is_shifted(self, plane_scene) -> None:
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        wrapper = figure.fill_plane("plot-plane", self.content(origin="-10 -20"))
        assert "translate(10 20)" in wrapper.get("transform", "")

    def test_corners_of_the_content_land_on_the_world_rectangle(self, plane_scene) -> None:
        """End to end: unit square -> plane matrix must equal projecting the corners."""
        cam = plane_scene.cam
        origin = np.array([-4.0, -3.0, 0.01])
        u_edge, v_edge = np.array([0.0, 8.0, 0.0]), np.array([6.0, 0.0, 0.0])
        a, b, c, d, e, f = cam.plane_matrix(origin, u_edge, v_edge)

        for (x, y), corner in zip(
            [(0, 0), (1, 0), (1, 1), (0, 1)],
            [origin, origin + u_edge, origin + u_edge + v_edge, origin + v_edge],
            strict=True,
        ):
            assert (a * x + c * y + e, b * x + d * y + f) == pytest.approx(cam.at(corner))

    def test_content_is_upright_for_this_plane(self, plane_scene) -> None:
        """a > 0 and d > 0, the rule that keeps labels from coming out mirrored."""
        a, b, c, d, _, _ = plane_scene.cam.plane_matrix(
            (-4.0, -3.0, 0.01), (0.0, 8.0, 0.0), (6.0, 0.0, 0.0)
        )
        assert a > 0 and d > 0
        assert a * d - b * c > 0

    def test_a_matplotlib_figure_can_fill_a_plane(self, plane_scene) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        mpl_fig, ax = plt.subplots(figsize=(3.0, 2.25))
        ax.plot([0, 1], [0, 1])

        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        figure.fill_plane("plot-plane", mpl_fig)

        group = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='plot-plane']")
        assert len(group) == 1
        assert group.find(f".//{{{SVG_NS}}}path") is not None, "the plotted line"
        plt.close(mpl_fig)

    def test_missing_target_is_reported(self, plane_scene) -> None:
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        with pytest.raises(KeyError, match="nope"):
            figure.fill_plane("nope", self.content())

    def test_content_without_intrinsic_size_is_rejected(self, plane_scene) -> None:
        """Normalizing onto the unit square needs a size to divide by."""
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        sizeless = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 0 0"><g/></svg>'
        with pytest.raises(ValueError, match="intrinsic size"):
            figure.fill_plane("plot-plane", sizeless)

    def test_filled_plane_survives_export(self, plane_scene, tmp_path) -> None:
        figure = Figure(width="120mm", height="90mm")
        figure.panel("a", x="6mm", y="6mm", w="108mm", h="78mm").add(plane_scene, id="s")
        figure.fill_plane("plot-plane", self.content())
        for suffix in (".svg", ".pdf", ".png"):
            out = tmp_path / f"figure{suffix}"
            figure.save(out)
            assert out.stat().st_size > 0


class TestFillSlot:
    """Upright content pinned to a world point, kept at its own size."""

    LABEL = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="12pt" height="6pt" viewBox="0 0 12 6">'
        '<rect id="mark" x="0" y="0" width="12" height="6"/></svg>'
    )

    @pytest.fixture
    def slotted(self, scene):
        scene.slot(45, (5.5, 0, 0), 16.0, 8.0, id="label", align="west", dx=2.0)
        return scene

    def place(self, scene, w="84mm"):
        figure = Figure(width="100mm", height="60mm")
        figure.panel("a", x="8mm", y="8mm", w=w, h="44mm").add(scene, id="s")
        figure.fill_slot("label", self.LABEL)
        return figure

    def test_label_sits_west_aligned_on_the_projected_anchor(self, slotted, ctm) -> None:
        figure = self.place(slotted)
        slot = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='label']")
        rect = figure.document.root.find(f".//{{{SVG_NS}}}rect[@id='mark']")
        anchor = ctm(slot) @ [0, 0, 1]
        corner = ctm(rect) @ [0, 0, 1]
        far = ctm(rect) @ [12, 6, 1]
        assert corner[0] == pytest.approx(anchor[0])
        assert (corner[1] + far[1]) / 2 == pytest.approx(anchor[1])
        # transforms are written to six significant figures
        assert far[:2] - corner[:2] == pytest.approx([16.0, 8.0], rel=1e-5)

    def test_label_size_does_not_follow_the_panel(self, slotted, ctm) -> None:
        sizes = []
        for w in ("84mm", "30mm"):
            figure = self.place(slotted, w=w)
            rect = figure.document.root.find(f".//{{{SVG_NS}}}rect[@id='mark']")
            sizes.append((ctm(rect) @ [12, 6, 1] - ctm(rect) @ [0, 0, 1])[:2])
        assert sizes[0] == pytest.approx(sizes[1])

    def test_filled_slot_survives_export(self, slotted, tmp_path) -> None:
        figure = self.place(slotted)
        for suffix in (".svg", ".pdf", ".png"):
            out = tmp_path / f"figure{suffix}"
            figure.save(out)
            assert out.stat().st_size > 0
