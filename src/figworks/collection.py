"""Regenerate a set of figures from one command.

A *collection* is one set of figures sharing a style, an output directory, and
a list of formats -- a thesis, a paper, a talk.  Register each figure once, and
the collection builds, saves, and closes them:

    HERE = Path(__file__).resolve().parent

    THESIS = FigureCollection(
        outdir=HERE / "figures",
        theme="paper",                       # typeface and base size
        style_file=HERE / "thesis.mplstyle",  # optional: lines, colours
    )

    @THESIS.figure("majorana_network")
    def majorana_network() -> Figure:
        ...

    if __name__ == "__main__":
        THESIS.main()

A builder returns either a FigWorks :class:`~figworks.Figure` or a Matplotlib
figure, and knows nothing about file paths.  Both kinds are written as vector
files where the format allows, byte-identically from run to run, and only after
their fonts are checked.  Each collection has its own registry, so a second
one -- slides with a larger theme, say -- can coexist without mixing figures.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from figworks.figure.figure import Theme

# A builder takes no arguments and returns the finished figure.  The collection
# owns styling, saving, and closing, so builders stay free of file paths.
type FigureBuilder = Callable[[], Any]

# PDF for LaTeX, SVG for hand editing, PNG for slides and quick previews.
DEFAULT_FORMATS: tuple[str, ...] = ("pdf", "svg", "png")


def git_revision(cwd: Path) -> str:
    """Short commit the figures were generated from, for provenance."""
    git = shutil.which("git")
    if git is None:
        return "unknown"
    try:
        out = subprocess.run(
            [git, "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return out.stdout.strip() or "unknown"


@dataclass
class FigureCollection:
    """One set of figures sharing a style, an output directory, and formats.

    Args:
        outdir: Where the files are written, one per figure and format.
        theme: The FigWorks theme whose typeface and base size every
            Matplotlib figure in the set uses, applied over ``style_file``.
        style_file: Optional Matplotlib style sheet for plot cosmetics -- line
            widths, colour cycle, legend frames.  Fonts come from ``theme``.
        formats: File formats to write, from ``svg``, ``pdf``, and ``png``.
        dpi: Resolution of PNG output.
    """

    outdir: Path
    theme: str | Theme = "paper"
    style_file: Path | None = None
    formats: Sequence[str] = DEFAULT_FORMATS
    dpi: int = 300
    builders: dict[str, FigureBuilder] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        unknown = sorted(set(self.formats) - {"svg", "pdf", "png"})
        if unknown:
            raise ValueError(f"unsupported format(s): {', '.join(unknown)}")

    def figure(self, name: str) -> Callable[[FigureBuilder], FigureBuilder]:
        """Register a figure builder under its output file name, without suffix."""

        def decorator(func: FigureBuilder) -> FigureBuilder:
            if name in self.builders:
                raise ValueError(f"Figure {name!r} is already registered.")
            self.builders[name] = func
            return func

        return decorator

    def apply_style(self) -> None:
        """Set Matplotlib to this collection's style, from a clean slate.

        Matplotlib's defaults first, so a run never inherits settings left by
        an earlier import or notebook session; then the style sheet, if any;
        then the theme's typeface and size on top, so every figure in the set
        uses one face.  :meth:`build` restores the previous settings afterwards.
        """
        import matplotlib.pyplot as plt

        from figworks.matplotlib import theme_rc

        plt.style.use("default")
        if self.style_file is not None:
            if not self.style_file.is_file():
                raise FileNotFoundError(f"Missing style sheet: {self.style_file}")
            plt.style.use(self.style_file)
        plt.rcParams.update(theme_rc(self.theme))

    def save_figure(self, name: str, fig: Any, outdir: Path | None = None) -> list[Path]:
        """Write one figure once per format; returns the paths written."""
        import matplotlib as mpl

        from figworks.figure.figure import Figure
        from figworks.matplotlib import save_figure

        outdir = outdir or self.outdir
        outdir.mkdir(parents=True, exist_ok=True)
        written = []
        for suffix in self.formats:
            path = outdir / f"{name}.{suffix}"
            if isinstance(fig, Figure):
                fig.save(path, dpi=self.dpi)
            elif isinstance(fig, mpl.figure.Figure):
                save_figure(fig, path, dpi=self.dpi)
            else:
                raise TypeError(
                    f"figure {name!r} returned {type(fig).__name__}; a builder must "
                    "return a FigWorks Figure or a Matplotlib figure"
                )
            written.append(path)
        return written

    def build(self, names: Sequence[str], outdir: Path | None = None) -> list[Path]:
        """Build and save the named figures in the order given; returns the paths.

        Matplotlib's settings are restored afterwards, so building from a
        notebook leaves its style alone.
        """
        import matplotlib as mpl
        import matplotlib.pyplot as plt

        written: list[Path] = []
        with plt.rc_context():
            self.apply_style()
            for name in names:
                fig = self.builders[name]()
                try:
                    paths = self.save_figure(name, fig, outdir)
                finally:
                    if isinstance(fig, mpl.figure.Figure):
                        plt.close(fig)
                    # Plots placed into a FigWorks figure stay open otherwise.
                    plt.close("all")
                written += paths
                print(f"  {name}: " + ", ".join(p.name for p in paths))
        return written

    def main(self, argv: Sequence[str] | None = None) -> None:
        """Command-line entry point: ``--list``, ``--all``, or figure names."""
        import matplotlib

        # Headless here, not on import: a notebook importing FigWorks keeps its backend.
        matplotlib.use("Agg")
        prog = Path(sys.argv[0]).name
        parser = argparse.ArgumentParser(prog=prog, description="Regenerate registered figures.")
        parser.add_argument(
            "names", nargs="*", help="figures to build (default: none; use --all or --list)"
        )
        parser.add_argument("--all", action="store_true", help="build every figure")
        parser.add_argument("--list", action="store_true", help="list registered figures and exit")
        parser.add_argument(
            "--outdir",
            type=Path,
            default=self.outdir,
            help=f"output directory (default: {self.outdir})",
        )
        args = parser.parse_args(argv)

        if not self.builders:
            parser.error("no figures are registered in this collection")

        if args.list:
            for name, func in sorted(self.builders.items()):
                summary = (func.__doc__ or "").strip().splitlines()
                print(f"{name:<24} {summary[0] if summary else ''}")
            return

        names = sorted(self.builders) if args.all else list(args.names)
        if not names:
            parser.error("no figures requested; pass names, --all, or --list")
        unknown = [name for name in names if name not in self.builders]
        if unknown:
            parser.error(
                f"unknown figure(s): {', '.join(unknown)}\n"
                f"registered: {', '.join(sorted(self.builders))}"
            )

        revision = git_revision(Path.cwd())
        print(f"Generating {len(names)} figure(s) at revision {revision}")
        written = self.build(names, args.outdir)
        print(f"Wrote {len(written)} file(s) to {args.outdir}")
