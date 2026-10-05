"""Placing a cirquit circuit.

cirquit is an optional source, not a dependency: FigForge places any object
exposing ``to_svg_document()``, so these tests skip when it is absent.
"""

from __future__ import annotations

import pytest

from figforge import Figure
from figforge.core.element import SVG_NS, resolve_svg_source, svg_intrinsic_size

cirquit = pytest.importorskip("cirquit", reason="cirquit is an optional source")


def build_circuit(**kwargs):
    """An LC loop: shunt capacitor on the left, inductor on the right."""
    circuit = cirquit.Circuit(72, 100, **kwargs)
    circuit.row(12, top_left=16, top_right=56, dots={"top_left"})
    circuit.row(88, bottom_left=16, bottom_right=56)
    circuit.wire("top_left", "top_right", id="upper-rail")
    circuit.wire("bottom_left", "bottom_right", id="lower-rail")
    circuit.capacitor("top_left", "bottom_left", id="C")
    circuit.inductor("top_right", "bottom_right", id="L")
    circuit.label("C", (6, 50), id="label-C", anchor="rc")
    return circuit


@pytest.fixture
def circuit():
    return build_circuit()


def place(source, id="lc"):
    figure = Figure(width="100mm", height="60mm")
    group = figure.panel("a", x="8mm", y="8mm", w="40mm", h="44mm").add(source, id=id)
    return figure, group


def test_circuit_satisfies_the_svg_document_protocol(circuit):
    assert resolve_svg_source(circuit) == circuit.to_svg_document()


def test_intrinsic_size_comes_from_the_circuit_viewbox(circuit):
    assert svg_intrinsic_size(circuit.to_svg_document()) == (72.0, 100.0, 0.0, 0.0)


def test_circuit_ids_survive_placement(circuit):
    figure, _ = place(circuit)

    figure.select("#L").set_style(stroke="navy")
    inductor = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='L']")
    assert inductor is not None
    assert "navy" in inductor.get("style", "")


def test_component_metadata_survives_placement(circuit):
    """``data-component`` lets downstream tooling tell symbols apart."""
    figure, _ = place(circuit)

    kinds = {
        node.get("id"): node.get("data-component")
        for node in figure.document.root.iter()
        if node.get("data-component")
    }
    assert kinds["C"] == "capacitor"
    assert kinds["L"] == "inductor"


def test_placement_scales_uniformly(circuit):
    """A per-axis scale would distort capacitor plates and inductor loops."""
    _, group = place(circuit)

    scale = group.get("transform", "").split("scale(")[1].split(")")[0]
    assert len(scale.split()) == 1, f"expected one uniform scale factor, got {scale!r}"


def test_circuit_survives_export(circuit, tmp_path):
    figure, _ = place(circuit)

    for suffix in (".svg", ".pdf", ".png"):
        out = tmp_path / f"figure{suffix}"
        figure.save(out)
        assert out.stat().st_size > 0


def test_placement_is_deterministic():
    first, _ = place(build_circuit())
    second, _ = place(build_circuit())
    assert first.document.to_string() == second.document.to_string()


def test_duplicate_ids_across_circuits_collide():
    """Known limitation: imported ids are copied verbatim, without namespacing.

    cirquit names node groups after their nodes, so two circuits built from the
    same node names both carry ``id="top_left"`` once placed, and ``#top_left``
    matches the first. Use distinct node and component ids per circuit until
    FigForge rewrites ids on import.
    """
    figure = Figure(width="100mm", height="60mm")
    figure.panel("a", x="5mm", y="5mm", w="40mm", h="50mm").add(build_circuit(), id="lc1")
    figure.panel("b", x="55mm", y="5mm", w="40mm", h="50mm").add(build_circuit(), id="lc2")

    ids = [node.get("id") for node in figure.document.root.iter() if node.get("id")]
    assert ids.count("L") == 2, "documents the collision; update when ids are rewritten"
