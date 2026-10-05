import pytest
from PIL import Image

from figworks import Figure


def test_svg_export(tmp_path):
    fig = Figure(width="100px", height="50px")
    fig.text("hello", x=10, y=20, id="caption")
    output = tmp_path / "figure.svg"

    fig.save(output)

    assert output.exists()
    assert 'id="caption"' in output.read_text(encoding="utf-8")


def test_pdf_and_png_export(tmp_path):
    fig = Figure(width="100px", height="50px")
    fig.text("hello", x=10, y=20, id="caption")
    pdf = tmp_path / "figure.pdf"
    png = tmp_path / "figure.png"

    fig.save(pdf)
    fig.save(png)

    assert pdf.exists()
    assert png.exists()


@pytest.mark.parametrize(
    ("width", "height"),
    [(96, 48), ("96px", "48px"), ("1in", "0.5in"), ("25.4mm", "12.7mm"), ("72pt", "36pt")],
)
def test_png_is_rasterized_at_dpi_whatever_the_unit(tmp_path, width, height):
    """One inch at 600 dpi is 600 pixels, whether the size was given in px or mm."""
    fig = Figure(width=width, height=height)
    fig.text("hello", x=10, y=20)
    png = tmp_path / "figure.png"

    fig.save(png, dpi=600)

    assert Image.open(png).size == (600, 300)
