"""FigureCollection: build both kinds of figure, deterministically, in the set's style."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from figworks import Figure, FigureCollection


def collection(tmp_path: Path, **kwargs: object) -> FigureCollection:
    figures = FigureCollection(outdir=tmp_path / "out", **kwargs)  # type: ignore[arg-type]

    @figures.figure("plot")
    def plot() -> plt.Figure:
        """A plain Matplotlib figure."""
        fig, ax = plt.subplots(figsize=(2, 1.5))
        ax.plot([0, 1], [0, 1])
        ax.set_xlabel(r"$\omega$")
        return fig

    @figures.figure("composed")
    def composed() -> Figure:
        """A FigWorks figure with a plot in a panel."""
        canvas = Figure(width="60mm", height="40mm")
        panel = canvas.panel("a", x="10mm", y="5mm", w="45mm", h="28mm")
        mpl_fig, ax = panel.subplots()
        ax.plot([0, 1], [1, 0])
        panel.add(mpl_fig, id="plot", fit="axes")
        canvas.label("a", anchor=panel.nw)
        return canvas

    return figures


def test_both_kinds_are_written_in_every_format(tmp_path: Path) -> None:
    written = collection(tmp_path).build(["plot", "composed"])
    names = sorted(path.name for path in written)
    assert names == sorted(
        f"{name}.{suffix}" for name in ("plot", "composed") for suffix in ("pdf", "svg", "png")
    )
    assert all(path.stat().st_size > 0 for path in written)


def test_a_composed_figure_stays_vector(tmp_path: Path) -> None:
    collection(tmp_path, formats=("svg",)).build(["composed"])
    svg = (tmp_path / "out" / "composed.svg").read_text(encoding="utf-8")
    assert "<image" not in svg, "no rasterized bridge"
    assert 'id="plot"' in svg


def test_rebuilding_writes_identical_bytes(tmp_path: Path) -> None:
    """Dates in PDF and SVG would differ a second apart; nothing may."""
    first = collection(tmp_path / "1").build(["plot", "composed"])
    time.sleep(1.1)
    second = collection(tmp_path / "2").build(["plot", "composed"])
    for a, b in zip(first, second, strict=True):
        assert a.read_bytes() == b.read_bytes(), a.name


def test_the_theme_face_overrides_the_style_sheet(tmp_path: Path) -> None:
    style = tmp_path / "set.mplstyle"
    style.write_text("font.family : serif\nlines.linewidth : 3.5\n", encoding="utf-8")
    figures = FigureCollection(outdir=tmp_path / "out", style_file=style, formats=("svg",))
    seen: dict[str, object] = {}

    @figures.figure("probe")
    def probe() -> plt.Figure:
        seen["family"] = list(plt.rcParams["font.family"])
        seen["linewidth"] = plt.rcParams["lines.linewidth"]
        return plt.figure()

    figures.build(["probe"])
    assert seen == {"family": ["TeX Gyre Heros"], "linewidth": 3.5}


def test_building_restores_matplotlib_settings(tmp_path: Path) -> None:
    before = plt.rcParams["font.family"]
    collection(tmp_path, formats=("svg",)).build(["plot"])
    assert plt.rcParams["font.family"] == before


def test_importing_figworks_leaves_the_backend_alone() -> None:
    code = "import matplotlib; import figworks; print(matplotlib.rcParams['backend'])"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env={"MPLBACKEND": "svg", "PATH": ""},
    )
    assert result.stdout.strip() == "svg"


def test_a_builder_must_return_a_figure(tmp_path: Path) -> None:
    figures = FigureCollection(outdir=tmp_path)
    figures.figure("bad")(lambda: "not a figure")
    with pytest.raises(TypeError, match="must return"):
        figures.build(["bad"])


def test_registration_and_formats_are_validated(tmp_path: Path) -> None:
    figures = collection(tmp_path)
    with pytest.raises(ValueError, match="already registered"):
        figures.figure("plot")(lambda: None)
    with pytest.raises(ValueError, match="unsupported format"):
        FigureCollection(outdir=tmp_path, formats=("gif",))


def test_command_line_lists_builds_and_rejects(tmp_path: Path, capsys) -> None:
    figures = collection(tmp_path)
    figures.main(["--list"])
    listing = capsys.readouterr().out
    assert "plot" in listing and "A plain Matplotlib figure." in listing

    figures.main(["plot", "--outdir", str(tmp_path / "cli")])
    assert (tmp_path / "cli" / "plot.svg").exists()

    for argv in ([], ["nope"]):
        with pytest.raises(SystemExit):
            figures.main(argv)
