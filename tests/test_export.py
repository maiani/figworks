from figforge import Figure


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
