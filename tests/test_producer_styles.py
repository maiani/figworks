"""One physical typography expressed in each producer's native settings."""

from dataclasses import replace

import pytest
from lxml import etree

from figworks import Figure, load_theme


@pytest.mark.parametrize("unit, factor", [("pt", 1), ("px", 96 / 72), ("mm", 25.4 / 72)])
def test_circuit_units_preserve_physical_sizes(unit, factor):
    theme = load_theme()
    assert theme.vecwire(unit=unit)["stroke_width"] == pytest.approx(theme.line.data * factor)
    assert theme.vecwire_label(unit=unit)["size"] == pytest.approx(theme.font.size * factor)
    assert theme.vecwire_label("tick", unit=unit)["size"] == pytest.approx(theme.font.tick * factor)


def test_settings_share_font_ink_and_physical_size():
    theme = load_theme()
    assert theme.rc()["font.size"] == theme.vectex()["size_pt"] == 8
    assert theme.vecview_text()["size"] == theme.plotly()["layout"]["font"]["size"] == 8 * 96 / 72
    assert theme.vecwire_label()["font_family"] == theme.vecview_text()["font_family"]
    assert theme.vecwire_label()["color"] == theme.vectex()["color"] == theme.color["ink"]
    template = theme.plotly()
    assert template["layout"]["xaxis"]["linecolor"] == theme.color["ink"]
    template["layout"]["xaxis"]["tickfont"]["size"] = 99
    assert template["layout"]["yaxis"]["tickfont"]["size"] != 99
    assert theme.plotly()["layout"]["xaxis"]["tickfont"]["size"] != 99


def test_custom_tex_style_is_explicit(tmp_path):
    path = tmp_path / "style.md"
    path.write_text("""---
font:
  family: Custom Font
tex:
  engine: lualatex
  preamble: |
    \\documentclass{standalone}
    \\usepackage{fontspec}
    \\setmainfont{Custom Font}
---
""")
    theme = load_theme(path)
    assert theme.vectex()["engine"] == "lualatex"
    assert "Custom Font" in theme.vectex()["preamble"]
    theme = replace(theme, tex={})
    with pytest.raises(ValueError, match=r"tex\.preamble"):
        theme.vectex()


@pytest.mark.parametrize("tex", ["[]", "{unknown: value}", "{engine: 1}", "{preamble: ''}"])
def test_invalid_tex_configuration(tmp_path, tex):
    path = tmp_path / "style.md"
    path.write_text(f"---\ntex: {tex}\n---\n")
    with pytest.raises(ValueError, match="tex"):
        load_theme(path)


def test_bad_role_and_unit_are_rejected():
    theme = load_theme()
    with pytest.raises(KeyError):
        theme.vecview_text("caption_typo")
    with pytest.raises(ValueError, match="unit"):
        theme.vecwire(unit="em")


def test_vecwire_font_and_size_survive_natural_placement():
    wire = pytest.importorskip("vecwire")
    theme = load_theme()
    circuit = wire.Circuit(100, 40, **theme.vecwire())
    circuit.label("Capacitance", (50, 20), id="cap-label", **theme.vecwire_label())
    figure = Figure(300, 200)
    group = figure.panel("circuit", 0, 0, 300, 200).add(circuit, id="c", fit="none")
    text = group.xpath(".//*[local-name()='text']")[0]
    assert text.get("font-family") == theme.font.family
    assert float(text.get("font-size")) == 8
    assert "scale(1.33333" in group.get("transform")


def test_vecview_text_uses_screen_pixels():
    view = pytest.importorskip("vecview")
    theme = load_theme()
    scene = view.Scene(view.OrthographicCamera(30, 25, 1))
    scene.text2d(1, 0, 0, "Device", **theme.vecview_text())
    root = etree.fromstring(scene.to_svg_document().encode())
    text = root.xpath("//*[local-name()='text']")[0]
    assert text.get("font-family") == theme.font.family
    assert float(text.get("font-size")) == pytest.approx(theme.px("font.size"), rel=1e-5)


def test_plotly_accepts_template_and_explicit_overrides():
    go = pytest.importorskip("plotly.graph_objects")
    theme = load_theme()
    plot = go.Figure(go.Scatter(x=[0, 1], y=[0, 1]))
    plot.update_layout(template=theme.plotly(), font_size=20)
    assert plot.layout.template.layout.font.size == theme.px("font.size")
    assert plot.layout.font.size == 20
