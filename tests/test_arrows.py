from pathlib import Path

import pytest

from figworks import Figure, load_theme


def heads(figure: Figure) -> dict[str, str]:
    """Each arrow's id, to the fill of the head it ends in."""
    root = figure.document.root
    markers = {m.get("id"): m[0].get("fill") for m in root.iter("{*}marker")}
    return {
        line.get("id"): markers[line.get("marker-end")[5:-1]]
        for line in root.iter("{*}line")
        if line.get("marker-end")
    }


def test_each_arrow_ends_in_a_head_of_its_own_colour() -> None:
    figure = Figure(width="40mm", height="20mm")
    figure.arrow("first", ("2mm", "5mm"), ("20mm", "5mm"), stroke="#c2185b")
    figure.arrow("second", ("2mm", "10mm"), ("20mm", "10mm"))
    figure.arrow("third", ("2mm", "15mm"), ("20mm", "15mm"), stroke="#c2185b")
    assert heads(figure) == {"first": "#c2185b", "second": "#000000", "third": "#c2185b"}
    assert len(list(figure.document.root.iter("{*}marker"))) == 2, "one head per colour"


def test_the_style_shapes_the_head(tmp_path: Path) -> None:
    style = tmp_path / "style.md"
    style.write_text("---\narrow:\n  head_length: 6\n  head_width: 4\n---\n")
    figure = Figure(width="40mm", height="20mm", theme=style)
    figure.arrow("a", ("2mm", "5mm"), ("20mm", "5mm"))
    (marker,) = figure.document.root.iter("{*}marker")
    assert (marker.get("markerWidth"), marker.get("markerHeight")) == ("6", "4")
    assert marker[0].get("d") == "M 0 0 L 6 2 L 0 4 z"
    assert load_theme("paper").arrow.head_length == 8


@pytest.mark.parametrize("value", ["8pt", 0, -2, "wide"])
def test_arrow_tokens_are_validated(tmp_path: Path, value: object) -> None:
    style = tmp_path / "style.md"
    style.write_text(f"---\narrow:\n  head_length: {value!r}\n---\n")
    with pytest.raises(ValueError, match=r"arrow\.head_length"):
        load_theme(style)
