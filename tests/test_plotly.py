import builtins
import os
import shutil

import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import _references
from figworks.plotly import plotly_to_svg

pio = pytest.importorskip("plotly.io")
go = pytest.importorskip("plotly.graph_objects")
pytest.importorskip("kaleido")


def test_export_normalizes_ids_and_references_without_changing_text(monkeypatch):
    def render(figure, **kwargs):
        assert kwargs == {"format": "svg", "width": 400, "height": 250, "scale": 1}
        return b"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="250"
          viewBox="0 0 400 250"><defs><clipPath id="random"><rect width="5"/>
          </clipPath></defs><g class="trace scatter traceabcdef" clip-path="url(#random)">
          <text>random traceabcdef</text><use href="#random"/></g></svg>"""

    monkeypatch.setattr(pio, "to_image", render)
    root = etree.fromstring(plotly_to_svg({}, width=400, height=250).encode())
    assert root.xpath("//@id") == ["plotly-0"]
    assert _references(root) == {"plotly-0"}
    assert root.xpath("//@class") == ["trace scatter traceuid0"]
    assert "random traceabcdef" in "".join(root.itertext())


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "400"])
@pytest.mark.parametrize("dimension", ["width", "height"])
def test_invalid_dimensions(value, dimension):
    with pytest.raises(ValueError, match=f"{dimension} must be a positive integer"):
        plotly_to_svg({}, **{dimension: value})


def test_missing_dependency_has_install_hint(monkeypatch):
    original = builtins.__import__

    def importing(name, *args, **kwargs):
        if name == "kaleido":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    with pytest.raises(ImportError, match=r"figworks\[plotly\]"):
        plotly_to_svg({})


def test_real_export_is_repeatable_editable_and_composable(tmp_path):
    if not os.environ.get("BROWSER_PATH") and not any(
        shutil.which(name) for name in ("google-chrome", "chromium", "chromium-browser", "chrome")
    ):
        pytest.skip("Chrome/Chromium is required for the real Plotly export test")
    plot = go.Figure(go.Scatter(x=[0, 1, 2], y=[0, 1, 0], mode="lines+markers"))
    plot.update_layout(font_family="DejaVu Sans", xaxis_title="Time", template="simple_white")
    before = plot.to_json()
    first = plotly_to_svg(plot, width=400, height=250)
    assert first == plotly_to_svg(plot.to_dict(), width=400, height=250)
    assert plot.to_json() == before
    root = etree.fromstring(first.encode())
    assert root.get("viewBox") == "0 0 400 250"
    assert root.xpath("//*[local-name()='text']")
    assert root.xpath("//*[local-name()='path']")
    assert not root.xpath("//*[local-name()='image']")
    assert _references(root) <= set(root.xpath("//@id"))

    figure = Figure(800, 250)
    figure.panel("left", 0, 0, 400, 250).add(first, id="first")
    plot.update_traces(y=[0, -1, 0])
    second = plotly_to_svg(plot, width=400, height=250)
    figure.panel("right", 400, 0, 400, 250).add(second, id="second")
    assembled = figure.document.root
    ids = assembled.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert _references(assembled) <= set(ids)
    for extension in ("svg", "pdf", "png"):
        output = tmp_path / f"plotly.{extension}"
        figure.save(output)
        assert output.stat().st_size > 100


def test_real_heatmap_colorbar_is_repeatable():
    if not os.environ.get("BROWSER_PATH") and not any(
        shutil.which(name) for name in ("google-chrome", "chromium", "chromium-browser", "chrome")
    ):
        pytest.skip("Chrome/Chromium is required for the real Plotly export test")
    plot = go.Figure(go.Heatmap(z=[[1, 2], [3, 4]]))
    first = plotly_to_svg(plot)
    assert first == plotly_to_svg(plot)
    root = etree.fromstring(first.encode())
    assert _references(root) <= set(root.xpath("//@id"))
    assert root.xpath("//*[local-name()='linearGradient']")
