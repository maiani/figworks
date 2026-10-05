"""style.md: one document for a publication's look, generating Matplotlib settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc


def write(path: Path, frontmatter: str, body: str = "# Style guide\n") -> Path:
    path.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return path


def test_the_built_in_paper_style_sets_every_token() -> None:
    paper = load_theme("paper")
    assert paper.font.family == "TeX Gyre Heros"
    assert (paper.font.size, paper.font.tick, paper.font.panel_label) == (8.0, 7.0, 10.0)
    assert (paper.line.data, paper.line.frame, paper.line.hairline) == (1.0, 0.5, 0.25)
    assert paper.color["ink"] == "#000000"


def test_presentation_inherits_what_it_does_not_override() -> None:
    presentation = load_theme("presentation")
    assert presentation.font.size == 11.0
    assert presentation.font.family == "TeX Gyre Heros"
    assert presentation.color == load_theme("paper").color


def test_a_style_states_only_its_differences(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "font:\n  size: 7pt\ncolor:\n  spin_up: '#d62828'\n")
    theme = load_theme(style)
    assert theme.font.size == 7.0
    assert theme.font.tick == 7.0, "unset sizes come from the base"
    assert theme.color == {"ink": "#000000", "neutral": "#737373", "spin_up": "#d62828"}


def test_bases_chain_and_paths_are_relative_to_each_file(tmp_path: Path) -> None:
    (tmp_path / "journal").mkdir()
    write(tmp_path / "journal" / "base.mplstyle", "")  # replaced below
    (tmp_path / "journal" / "base.mplstyle").write_text("lines.dashed_pattern : 3, 1\n")
    write(
        tmp_path / "journal" / "journal.md",
        "base: presentation\nmatplotlib: base.mplstyle\nfont:\n  size: 9pt\n",
    )
    chapter = write(tmp_path / "chapter.md", "base: journal/journal.md\nline:\n  data: 2pt\n")
    theme = load_theme(chapter)
    assert theme.font.size == 9.0 and theme.line.data == 2.0 and theme.font.tick == 10.0
    assert theme.matplotlib == (str((tmp_path / "journal" / "base.mplstyle").resolve()),)
    assert list(theme.rc()["lines.dashed_pattern"]) == [3.0, 1.0]


def test_units_are_converted_to_points(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "line:\n  frame: 0.2mm\n  data: 1\n")
    theme = load_theme(style)
    assert theme.line.frame == pytest.approx(0.2 / 25.4 * 72)
    assert theme.line.data == 1.0, "a bare number is points"


def test_tokens_generate_matplotlib_settings() -> None:
    rc = load_theme("paper").rc()
    assert rc["font.family"] == ["TeX Gyre Heros"]
    assert rc["mathtext.it"] == "TeX Gyre Heros:italic"
    assert (rc["xtick.labelsize"], rc["axes.labelsize"]) == (7.0, 8.0)
    assert (rc["lines.linewidth"], rc["axes.linewidth"], rc["grid.linewidth"]) == (1.0, 0.5, 0.25)
    assert rc["axes.edgecolor"] == "#000000"


def test_the_cycle_names_colours_by_role(tmp_path: Path) -> None:
    style = write(
        tmp_path / "style.md",
        "color:\n  spin_up: '#d62828'\n  spin_down: '#1f6fd1'\n"
        "cycle: [spin_up, spin_down, '#00aa00']\n",
    )
    rc = load_theme(style).rc()
    assert rc["axes.prop_cycle"].by_key()["color"] == ["#d62828", "#1f6fd1", "#00aa00"]


def test_rcparams_are_applied_last(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "rcparams:\n  lines.linewidth: 3\n  axes.grid: true\n")
    rc = load_theme(style).rc()
    assert rc["lines.linewidth"] == 3.0, "over the line.data token"
    assert rc["axes.grid"] is True


def test_named_matplotlib_styles_layer_under_the_tokens(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "matplotlib: ggplot\n")
    rc = load_theme(style).rc()
    assert rc["axes.facecolor"] == "#E5E5E5", "from ggplot"
    assert rc["font.family"] == ["TeX Gyre Heros"], "the tokens win"


def test_lengths_in_px_for_other_producers() -> None:
    paper = load_theme("paper")
    assert paper.px("line.frame") == pytest.approx(0.5 * 96 / 72)
    assert paper.px("font.size") == pytest.approx(8 * 96 / 72)
    assert paper.px("marker") == pytest.approx(3 * 96 / 72)
    with pytest.raises(KeyError):
        paper.px("font.family")


def test_figures_and_theme_rc_accept_a_style_file(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "font:\n  family: DejaVu Sans\n  panel_label: 12pt\n")
    figure = Figure(width=100, height=50, theme=style)
    assert figure.document.root.get("font-family") == "DejaVu Sans"
    assert figure.theme.panel_label_font_size == "12pt"
    assert theme_rc(style)["font.family"] == ["DejaVu Sans"]


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("# no frontmatter\n", "starts with"),
        ("---\nfont: {}\n", "not closed"),
        ("---\ncolours: {}\n---\n", "unknown key"),
        ("---\nfont:\n  weight: bold\n---\n", "unknown font token"),
        ("---\nline:\n  data: thick\n---\n", "line.data"),
        ("---\nbase: nowhere.md\n---\n", "no style"),
        ("---\nrcparams:\n  lines.thickness: 2\n---\n", "lines.thickness"),
        ("---\nmatplotlib: no-such-style\n---\n", "no Matplotlib style"),
        ("---\nbase: null\nfont: {}\n---\n", "not set anywhere"),
    ],
)
def test_mistakes_are_reported_clearly(tmp_path: Path, text: str, match: str) -> None:
    path = tmp_path / "style.md"
    path.write_text(text, encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError), match=match):
        load_theme(path).rc()


def test_a_cycle_of_bases_is_reported(tmp_path: Path) -> None:
    write(tmp_path / "a.md", "base: b.md\n")
    write(tmp_path / "b.md", "base: a.md\n")
    with pytest.raises(ValueError, match="cycle"):
        load_theme(tmp_path / "a.md")


@pytest.mark.parametrize(
    ("name", "column", "family", "smallest"),
    [
        ("nature", "89mm", "TeX Gyre Heros", 5.0),
        ("aps", "86mm", "TeX Gyre Heros", 7.0),
        ("ieee", "88.9mm", "TeX Gyre Termes", 6.0),
    ],
)
def test_journal_styles_meet_their_guidelines(
    name: str, column: str, family: str, smallest: float
) -> None:
    theme = load_theme(name)
    assert theme.page["column"] == column
    assert theme.font.family == family
    sizes = [theme.font.size, theme.font.label, theme.font.tick, theme.font.legend]
    assert min(sizes) >= smallest, "no text below the journal's minimum"
    theme.rc()


def test_aps_lines_meet_the_half_point_minimum() -> None:
    line = load_theme("aps").line
    assert min(line.data, line.frame, line.hairline) >= 0.5


def test_page_lengths_are_validated(tmp_path: Path) -> None:
    style = write(tmp_path / "style.md", "page:\n  column: wide\n")
    with pytest.raises(ValueError, match=r"page\.column"):
        load_theme(style)


def test_a_figure_can_be_sized_from_the_page() -> None:
    nature = load_theme("nature")
    figure = Figure(width=nature.page["column"], height="60mm", theme=nature)
    assert figure.document.root.get("width") == "89mm"
