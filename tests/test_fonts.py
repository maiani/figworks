"""The export-time font check, and the theme typeface that keeps a figure in one face."""

from __future__ import annotations

import re
import shutil

import matplotlib.pyplot as plt
import pytest

from figworks import Figure
from figworks.fonts import Face, FontError, ResolvedFace, check_fonts
from figworks.matplotlib import mpl_to_svg, theme_rc

ASCII = ((0x20, 0x7E),)


def svg(body: str, **root: str) -> str:
    attrs = "".join(f' {key.replace("_", "-")}="{value}"' for key, value in root.items())
    return f'<svg xmlns="http://www.w3.org/2000/svg"{attrs}>{body}</svg>'


class FakeFonts:
    """A resolver over a fixed table, recording what was asked for."""

    def __init__(self, table: dict[Face, ResolvedFace]) -> None:
        self.table = table
        self.asked: list[Face] = []

    def __call__(self, face: Face) -> ResolvedFace | None:
        self.asked.append(face)
        return self.table.get(face)


def face(family: str = "Heros", weight: str = "normal", style: str = "normal") -> Face:
    return Face(family, weight, style)


def resolved(
    family: str = "Heros", codepoints: tuple[tuple[int, int], ...] = ASCII
) -> ResolvedFace:
    return ResolvedFace(file=f"/fonts/{family}.otf", families=(family,), codepoints=codepoints)


def test_a_font_that_resolves_and_covers_the_text_passes() -> None:
    fonts = FakeFonts({face(): resolved()})
    check_fonts(svg("<text>x = 1</text>", font_family="Heros"), fonts)
    assert fonts.asked == [face()]


def test_font_properties_are_inherited_and_style_overrides_attributes() -> None:
    fonts = FakeFonts({face("Heros", "bold", "italic"): resolved()})
    body = '<g font-weight="bold"><text style="font-style: italic" font-style="normal">a</text></g>'
    check_fonts(svg(body, font_family="Heros"), fonts)
    assert fonts.asked == [face("Heros", "bold", "italic")]


def test_only_the_first_family_of_a_list_counts() -> None:
    """CairoSVG never falls back, so neither does the check."""
    fonts = FakeFonts({face("Heros"): resolved()})
    check_fonts(svg("<text font-family=\"'Heros', Arial, sans-serif\">a</text>"), fonts)
    assert fonts.asked == [face("Heros")]


def test_tspans_and_tails_are_checked_in_their_own_faces() -> None:
    fonts = FakeFonts({face(): resolved(), face(style="italic"): resolved()})
    body = '<text>a<tspan font-style="italic">b</tspan>c</text>'
    check_fonts(svg(body, font_family="Heros"), fonts)
    assert set(fonts.asked) == {face(), face(style="italic")}


def test_a_substituted_family_is_reported_with_what_it_would_become() -> None:
    fonts = FakeFonts({face("Heros"): resolved("EB Garamond")})
    with pytest.raises(FontError, match=r"Heros.*not installed.*EB Garamond"):
        check_fonts(svg("<text>a</text>", font_family="Heros"), fonts)


def test_a_missing_glyph_is_reported_by_code_point() -> None:
    fonts = FakeFonts({face(): resolved()})
    with pytest.raises(FontError, match=r"U\+03C6"):
        check_fonts(svg("<text>φ</text>", font_family="Heros"), fonts)


def test_a_generic_family_is_reported() -> None:
    with pytest.raises(FontError, match="generic family"):
        check_fonts(svg("<text>a</text>"), FakeFonts({}))


def test_every_problem_is_collected_into_one_error() -> None:
    fonts = FakeFonts({face(): resolved()})
    body = '<text>φ</text><text font-family="Nope">a</text><text font-family="serif">b</text>'
    with pytest.raises(FontError) as raised:
        check_fonts(svg(body, font_family="Heros"), fonts)
    assert len(str(raised.value).splitlines()) == 4  # header + three problems


def test_whitespace_needs_no_glyph() -> None:
    check_fonts(svg("<text> \n\t</text>"), FakeFonts({}))


def test_text_outside_text_elements_is_ignored() -> None:
    check_fonts(svg("<title>a caption</title><desc>notes</desc>"), FakeFonts({}))


def test_the_theme_face_is_set_on_the_root_for_sources_naming_none() -> None:
    figure = Figure(width=100, height=50)
    assert figure.document.root.get("font-family") == figure.theme.font_family == "TeX Gyre Heros"


def test_theme_rc_puts_plot_text_and_math_in_the_theme_face() -> None:
    # Math fonts are chosen at draw time, so the export must see the settings too.
    with plt.rc_context(theme_rc()):
        mpl_fig, ax = plt.subplots(figsize=(2, 1.5))
        ax.set_xlabel(r"$\omega$ (GHz)")
        document = mpl_to_svg(mpl_fig)
    plt.close(mpl_fig)
    families = {
        m.split(",")[0].strip("'\" ") for m in re.findall(r"font-family: ([^;\"]+)", document)
    }
    assert families == {"TeX Gyre Heros"}
    assert "font-style: italic" in document, "math is set in the italic face"


def test_theme_rc_uses_the_theme_size() -> None:
    assert theme_rc()["font.size"] == pytest.approx(8.0)
    assert theme_rc("presentation")["font.size"] == pytest.approx(11.0)


needs_fontconfig = pytest.mark.skipif(
    shutil.which("fc-match") is None or shutil.which("fc-query") is None,
    reason="fontconfig's command-line tools are not installed",
)


@needs_fontconfig
def test_saving_with_a_missing_font_raises_before_writing(tmp_path) -> None:
    figure = Figure(width=100, height=50)
    figure.text("hello", x=10, y=20, font_family="No Such Font 9000")
    for suffix in (".pdf", ".png"):
        out = tmp_path / f"figure{suffix}"
        with pytest.raises(FontError, match="No Such Font 9000"):
            figure.save(out)
        assert not out.exists()


@needs_fontconfig
def test_svg_is_written_whatever_its_fonts(tmp_path) -> None:
    figure = Figure(width=100, height=50)
    figure.text("hello", x=10, y=20, font_family="No Such Font 9000")
    figure.save(tmp_path / "figure.svg")
    assert (tmp_path / "figure.svg").exists()
