"""``math: latex``: Matplotlib typesets text with LaTeX, and FigWorks places the outlines.

These run LaTeX, so they skip without it and the packages the theme preambles
load; the CI job that installs TeX runs them.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pytest
from lxml import etree

from figworks import Figure, load_theme
from figworks.core.element import parse_svg
from figworks.fonts import check_fonts
from figworks.matplotlib import mpl_to_svg, theme_rc
from figworks.style import SCALABLE_CMEX

FACES = {
    "TeX Gyre Heros": ("tgheros.sty", "sansmath.sty"),
    "Latin Modern Sans": ("lmodern.sty", "sansmath.sty"),
}


def _installed(*files: str) -> bool:
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich is None:
        return False
    # Matplotlib's own usetex preamble loads type1cm and checks for cm-super.
    for name in ("type1cm.sty", "type1ec.sty", "amsmath.sty", *files):
        found = subprocess.run([kpsewhich, name], capture_output=True, text=True, check=False)
        if not found.stdout.strip():
            return False
    return True


pytestmark = pytest.mark.skipif(
    shutil.which("latex") is None, reason="Matplotlib's usetex needs latex"
)


def latex_style(tmp_path: Path, family: str) -> Path:
    if not _installed(*FACES[family]):
        pytest.skip(f"the TeX packages for {family} are not installed")
    path = tmp_path / "style.md"
    path.write_text(f"---\nfont:\n  family: {family}\nmath: latex\n---\n", encoding="utf-8")
    return path


def dvi_sizes(rc: dict, tex: str) -> dict[str, float]:
    """Each font's size in the DVI Matplotlib typesets for its SVG and PDF text-as-path."""
    from matplotlib import dviread
    from matplotlib.texmanager import TexManager
    from matplotlib.textpath import TextToPath

    with matplotlib.rc_context(rc):
        dvi = TexManager().make_dvi(tex, TextToPath.FONT_SCALE)
    with dviread.Dvi(dvi, 72) as pages:
        (page,) = pages
    return {text.font.texname.decode(): text.font.size for text in page.text}


@pytest.mark.parametrize("family", sorted(FACES))
def test_large_operators_scale_with_the_text(tmp_path, family) -> None:
    """Regression: ∫ and ∑ came out at a quarter size in SVG, PDF, and PNG."""
    sizes = dvi_sizes(load_theme(latex_style(tmp_path, family)).rc(), r"$\int K\,dx$")
    assert sizes.pop("cmex10") == pytest.approx(max(sizes.values()), rel=1e-3)


def test_amsmath_caps_cmex_without_the_declaration(tmp_path) -> None:
    """What the declaration fixes: without it cmex10 stops at 24.88 pt, not 100 pt."""
    rc = dict(load_theme(latex_style(tmp_path, "TeX Gyre Heros")).rc())
    rc["text.latex.preamble"] = rc["text.latex.preamble"].replace(SCALABLE_CMEX, "")
    sizes = dvi_sizes(rc, r"$\int K\,dx$")
    assert sizes.pop("cmex10") < 0.3 * max(sizes.values())


@pytest.mark.parametrize("family", sorted(FACES))
def test_a_latex_figure_has_no_live_plot_text_and_passes_the_checks(tmp_path, family) -> None:
    style = latex_style(tmp_path, family)
    fig = Figure("86mm", "40mm", theme=style)
    panel = fig.panel("a", x="12mm", y="4mm", w="70mm", h="28mm")
    with matplotlib.rc_context(theme_rc(style)):
        mpl_fig, ax = panel.subplots()
        ax.text(0.05, 0.6, r"$S(a)=\int K(x)[V'(x+a)-V'(x)]dx$")
        ax.text(0.05, 0.2, r"$\langle Y\rangle\propto \mathcal{Q}_3\sum_n \hbar\omega_n$")
        plot = parse_svg(mpl_to_svg(mpl_fig))
        panel.add(mpl_fig, id="plot", fit="axes")
    plt.close(mpl_fig)
    assert not list(plot.iter("{*}text")), "usetex text is glyph outlines"
    fig.label("a", ("2mm", "6mm"))
    document = fig.document.to_string()
    check_fonts(document)  # the panel label, live text in the theme face
    texts = list(etree.fromstring(document.encode()).iter("{*}text"))
    assert len(texts) == 1
    report = fig.check()
    assert report.ok, report.issues
    for suffix in (".pdf", ".png"):
        fig.save(tmp_path / f"figure{suffix}")
        assert (tmp_path / f"figure{suffix}").stat().st_size > 0
