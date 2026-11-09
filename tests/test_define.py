import pytest
import svg
from PIL import Image

from figworks import Figure
from figworks.core.element import local_name


def ramp(id: str = "ramp") -> svg.LinearGradient:
    return svg.LinearGradient(
        id=id,
        elements=[
            svg.Stop(offset=0, stop_color="black"),
            svg.Stop(offset=1, stop_color="black", stop_opacity=0),
        ],
    )


def test_definition_goes_to_defs_and_returns_its_reference():
    fig = Figure(width="100px", height="50px")

    paint = fig.define(ramp())
    fig.rect(x=0, y=0, width=100, height=50, fill=paint, id="lead")

    assert paint == "url(#ramp)"
    (gradient,) = fig.select("#ramp")
    assert local_name(gradient.getparent()) == "defs"
    assert [local_name(stop) for stop in gradient] == ["stop", "stop"]
    (lead,) = fig.select("#lead")
    assert lead.get("fill") == "url(#ramp)"


def test_definition_needs_a_new_id():
    fig = Figure(width="100px", height="50px")
    fig.rect(x=0, y=0, width=10, height=10, id="taken")

    with pytest.raises(ValueError, match="already used"):
        fig.define(ramp("taken"))
    with pytest.raises(ValueError, match="needs an id"):
        fig.define(svg.RadialGradient(elements=[svg.Stop(offset=0, stop_color="red")]))


def test_png_renders_a_defined_gradient(tmp_path):
    """Black on the left fading to the white page on the right, through CairoSVG."""
    fig = Figure(width="100px", height="20px", background="white")
    fig.rect(x=0, y=0, width=100, height=20, fill=fig.define(ramp()))
    png = tmp_path / "ramp.png"

    fig.save(png, dpi=96)

    with Image.open(png) as image:
        rgb = image.convert("RGB")
        left, middle, right = (rgb.getpixel((x, 10))[0] for x in (1, 50, 98))
    assert left < 20
    assert 100 < middle < 160
    assert right > 235


def test_nested_definition_ids_are_validated_before_modifying_the_figure():
    fig = Figure(100, 50)
    fig.rect(id="taken", x=0, y=0, width=10, height=10)
    before = fig.document.to_string()
    for children in (
        [svg.Rect(id="taken")],
        [svg.Rect(id="duplicate"), svg.Circle(id="duplicate")],
        [svg.Rect(id="two words")],
    ):
        with pytest.raises(ValueError):
            fig.define(svg.ClipPath(id="clip", elements=children))
        assert fig.document.to_string() == before
