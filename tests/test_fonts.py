"""The export-time font check, and the theme typeface that keeps a figure in one face."""

from __future__ import annotations

import re
import shutil

import matplotlib.pyplot as plt
import pytest

from figworks import Figure
from figworks.core.element import parse_svg
from figworks.fonts import (
    Face,
    FontError,
    ResolvedFace,
    check_fonts,
    expand_font_shorthand,
    for_cairosvg,
    parse_font_shorthand,
)
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


# --- the CSS font shorthand ------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("8px 'cmex10'", {"font-size": "8px", "font-family": "'cmex10'"}),
        (
            "italic 5.6px 'TeX Gyre Heros'",
            {"font-style": "italic", "font-size": "5.6px", "font-family": "'TeX Gyre Heros'"},
        ),
        (
            "oblique 700 8px 'DejaVu Sans', sans-serif",
            {
                "font-style": "oblique",
                "font-weight": "700",
                "font-family": "'DejaVu Sans', sans-serif",
            },
        ),
        ("bold 12px/1.2 Arial", {"font-weight": "bold", "font-size": "12px", "line-height": "1.2"}),
        (
            "bold 12px / 1.2 Arial",
            {"font-size": "12px", "line-height": "1.2", "font-family": "Arial"},
        ),
        (
            "small-caps condensed 8pt X, Y",
            {"font-variant": "small-caps", "font-stretch": "condensed"},
        ),
        ("normal italic 8px X", {"font-style": "italic", "font-weight": "normal"}),
        ("oblique 10deg 8px X", {"font-style": "oblique", "font-size": "8px", "font-family": "X"}),
        ("larger X", {"font-size": "larger"}),
    ],
)
def test_the_font_shorthand_is_read_by_the_css_grammar(value, expected) -> None:
    longhand = parse_font_shorthand(value)
    assert longhand is not None
    assert set(longhand) == {
        "font-style",
        "font-variant",
        "font-weight",
        "font-stretch",
        "font-size",
        "line-height",
        "font-family",
    }
    assert longhand.items() >= expected.items()


@pytest.mark.parametrize(
    "value",
    ["caption", "12px", "'X' 12px", "10 X", "700 bold 8px X", "calc(2px + 1em) X", "8px X,"],
)
def test_an_invalid_font_shorthand_is_not_guessed(value) -> None:
    assert parse_font_shorthand(value) is None


def test_the_shorthand_family_overrides_an_inherited_one() -> None:
    """Matplotlib before 3.10 writes only the shorthand; the root sets the theme face."""
    fonts = FakeFonts({face(): resolved(), face("cmex10"): None})
    body = "<text style=\"font: 8px 'cmex10'\">Z</text>"
    with pytest.raises(FontError, match=r"cmex10.*not installed"):
        check_fonts(svg(body, font_family="Heros"), fonts)
    assert fonts.asked == [face("cmex10")]


def test_the_shorthand_sets_style_and_resets_weight() -> None:
    fonts = FakeFonts({face("Heros", "normal", "italic"): resolved()})
    body = '<g font-weight="bold"><text style="font: italic 5.6px \'Heros\'">a</text></g>'
    check_fonts(svg(body), fonts)
    assert fonts.asked == [face("Heros", "normal", "italic")]


def test_later_declarations_override_earlier_ones() -> None:
    fonts = FakeFonts({face("Late"): resolved("Late"), face("After"): resolved("After")})
    check_fonts(svg('<text style="font-family: Early; font: 8px Late">a</text>'), fonts)
    check_fonts(svg('<text style="font: 8px Early; font-family: After">a</text>'), fonts)
    assert fonts.asked == [face("Late"), face("After")]


def test_an_unreadable_shorthand_is_a_problem() -> None:
    fonts = FakeFonts({face(): resolved()})
    with pytest.raises(FontError, match="cannot read this CSS font shorthand"):
        check_fonts(svg('<text style="font: caption">a</text>', font_family="Heros"), fonts)


def test_a_font_attribute_is_not_a_presentation_attribute() -> None:
    fonts = FakeFonts({face(): resolved()})
    check_fonts(svg('<text font="8px Other">a</text>', font_family="Heros"), fonts)
    assert fonts.asked == [face()]
    assert 'font="' not in for_cairosvg(svg('<text font="8px Other">a</text>'))


def test_weights_follow_cairosvg() -> None:
    fonts = FakeFonts({face(weight="600"): resolved(), face(weight="bolder"): resolved()})
    check_fonts(
        svg(
            '<text font-weight="600">a</text><text font-weight="bolder">b</text>',
            font_family="Heros",
        ),
        fonts,
    )
    with pytest.raises(FontError) as raised:
        check_fonts(
            svg(
                '<text font-family="Nope" font-weight="600">a</text>'
                '<text font-family="Nope" font-weight="bolder">b</text>'
            ),
            FakeFonts({}),
        )
    assert "Nope:weight=bold" in str(raised.value)
    assert "Nope:weight=regular" in str(raised.value)  # CairoSVG has no "bolder"


def test_expansion_keeps_other_declarations_in_place() -> None:
    root = parse_svg(
        svg("<text style=\"fill: red; font: italic 8px 'X'; text-anchor: end\">a</text>")
    )
    assert expand_font_shorthand(root) == []
    style = root[0].get("style")
    assert style.startswith("fill: red; font-style: italic")
    assert style.endswith("font-family: 'X'; text-anchor: end")
    assert for_cairosvg(svg("<text>no shorthand</text>")) == svg("<text>no shorthand</text>")


@needs_fontconfig
def test_export_draws_a_shorthand_run_in_the_face_it_names(tmp_path) -> None:
    """CairoSVG alone would draw it in the root's face, which it inherits."""
    from PIL import Image, ImageChops

    def render(text_style: str) -> Image.Image:
        figure = Figure(width=120, height=40)
        figure.document.root.append(
            parse_svg(svg(f'<text x="4" y="30" style="{text_style}">Hag</text>'))[0]
        )
        out = tmp_path / "text.png"
        figure.save(out, dpi=96)
        return Image.open(out).convert("RGBA")

    shorthand = render("font: 24px 'DejaVu Serif'")
    longhand = render("font-size: 24px; font-family: 'DejaVu Serif'")
    root_face = render("font-size: 24px")
    assert ImageChops.difference(shorthand, longhand).getbbox() is None
    assert ImageChops.difference(shorthand, root_face).getbbox() is not None


# --- math in the theme face, and what it cannot cover ----------------------

REPRO = (r"$S(a)=\int K(x)[V'(x+a)-V'(x)]dx$", r"$\langle Y\rangle\propto a^2\mathcal{Q}_3$")


def _repro_figure(math: str = "auto") -> Figure:
    """The documented workflow: theme_rc, Panel.subplots, fit="axes"."""
    import matplotlib

    fig = Figure("86mm", "40mm", theme="paper")
    panel = fig.panel("a", x="12mm", y="4mm", w="70mm", h="28mm")
    with matplotlib.rc_context(theme_rc("paper")):
        mpl_fig, ax = panel.subplots()
        ax.text(0.05, 0.6, REPRO[0])
        ax.text(0.05, 0.2, REPRO[1])
        if math == "auto":
            panel.add(mpl_fig, id="plot", fit="axes")
        else:
            fig.document.root.append(parse_svg(mpl_to_svg(mpl_fig, math=math)))
    plt.close(mpl_fig)
    return fig


def test_theme_math_takes_calligraphic_capitals_from_tex() -> None:
    assert theme_rc()["mathtext.cal"] == "cmsy10"
    assert theme_rc()["mathtext.fontset"] == "custom"


@needs_fontconfig
def test_math_the_text_face_cannot_cover_is_outlined_and_renders(tmp_path) -> None:
    """Regression: integral, prime, angle brackets, propto, and mathcal misprinted."""
    figure = _repro_figure()
    document = figure.document.to_string()
    check_fonts(document)  # every run left as text renders as written
    root = parse_svg(document)
    families = {
        node.get("style", "").split("font-family:")[-1].split(";")[0].strip(" '")
        for node in root.iter()
        if isinstance(node.tag, str) and "font-family:" in node.get("style", "")
    }
    assert families == {"TeX Gyre Heros"}, "only the tick labels stay live, in the theme face"
    assert len([n for n in root.iter("{*}text")]) == 12
    glyphs = {n.get("id", "").rsplit("-", 1)[0] for n in root.iter("{*}path")}
    assert {"Cmex10", "Cmsy10"} <= glyphs, "∫ and ⟨⟩ come from Computer Modern outlines"
    for suffix in (".pdf", ".png"):
        figure.save(tmp_path / f"repro{suffix}")
        assert (tmp_path / f"repro{suffix}").stat().st_size > 0


@needs_fontconfig
def test_math_kept_as_text_where_it_cannot_render_raises(tmp_path) -> None:
    figure = _repro_figure(math="text")
    with pytest.raises(FontError, match=r"cmex10.*not installed"):
        figure.save(tmp_path / "repro.pdf")
    assert not (tmp_path / "repro.pdf").exists()


@needs_fontconfig
def test_math_the_text_face_covers_stays_live_text() -> None:
    with plt.rc_context(theme_rc()):
        mpl_fig, ax = plt.subplots(figsize=(2, 1.5))
        ax.set_xlabel(r"$x^2 + y_1$ (m)")
        auto = mpl_to_svg(mpl_fig)
        outlined = mpl_to_svg(mpl_fig, math="path")
    plt.close(mpl_fig)
    assert ">x<" in auto.replace("</tspan>", "<").replace("\n", "")
    assert "TeXGyreHeros-Italic-" in outlined
    assert "TeXGyreHeros-Italic-" not in auto


def test_math_mode_is_validated() -> None:
    mpl_fig, _ = plt.subplots()
    with pytest.raises(ValueError, match="math must be"):
        mpl_to_svg(mpl_fig, math="mathml")  # ty: ignore[invalid-argument-type]
    plt.close(mpl_fig)
