"""Figure-collection machinery.

This module is the reusable part: it knows how to register a figure, apply a
style sheet, write the output files, and parse a command line.  It knows
nothing about the physics, and nothing about any particular thesis, paper, or
talk.

A *collection* is one set of figures that share a style and an output
directory.  It owns that configuration, so a collection file looks like:

    HERE = Path(__file__).resolve().parent

    THESIS = FigureCollection(
        name="thesis_plots.py",
        style_file=HERE / "thesis.mplstyle",
        outdir=HERE / "output_plots",
    )
    figure = THESIS.figure

    @figure("majorana_network")
    def majorana_network() -> Figure:
        ...

    if __name__ == "__main__":
        THESIS.main()

Because each collection carries its own registry, a second collection (say
`slides_plots.py`, with a larger-font style sheet) can coexist with the first
without their figures mixing.

Not meant to be run directly: `figforge/collection.py` defines no figures.
Run the collection file instead, e.g. `python examples/thesis_plots.py --all`.
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

# Headless backend: these figures are generated from a terminal or a Makefile,
# never interactively.
matplotlib.use("Agg")

import matplotlib.pyplot as plt

# A figure builder takes no arguments and returns the finished Figure.  The
# collection owns saving and closing, so builders stay free of file paths.
FigureBuilder = Callable[[], Any]

# PDF for LaTeX, SVG for hand editing, PNG for slides and quick previews.
DEFAULT_FORMATS: tuple[str, ...] = ("pdf", "svg", "png")


def git_revision(cwd: Path) -> str:
    """Short commit the figures were generated from, for provenance."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
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
    """One set of figures sharing a style sheet and an output directory."""

    name: str
    style_file: Path
    outdir: Path
    formats: Sequence[str] = DEFAULT_FORMATS
    builders: dict[str, FigureBuilder] = field(default_factory=dict)

    def figure(self, name: str) -> Callable[[FigureBuilder], FigureBuilder]:
        """Register a figure builder under the output file name (no suffix)."""

        def decorator(func: FigureBuilder) -> FigureBuilder:
            if name in self.builders:
                raise ValueError(f"Figure {name!r} is already registered.")
            self.builders[name] = func
            return func

        return decorator

    def apply_style(self, style_file: Path | None = None) -> None:
        """Load this collection's style from a Matplotlib style sheet.

        The style lives in a `.mplstyle` file rather than in Python so that it
        is declarative, reusable from a notebook (`plt.style.use(...)`), and
        diffable on its own.  We start from Matplotlib's defaults so a run
        never inherits rcParams left behind by an earlier import or notebook
        session.
        """
        style_file = style_file or self.style_file
        if not style_file.is_file():
            raise FileNotFoundError(f"Missing style sheet: {style_file}")

        plt.style.use("default")
        plt.style.use(style_file)

    def save_figure(self, name: str, fig: Any, outdir: Path | None = None) -> list[Path]:
        """Write one figure to `outdir` once per format of this collection."""
        outdir = outdir or self.outdir
        outdir.mkdir(parents=True, exist_ok=True)
        written = []

        for suffix in self.formats:
            path = outdir / f"{name}.{suffix}"
            # Resolution comes from `savefig.dpi` in the style sheet and only
            # affects the raster output; the vector formats ignore it.
            fig.savefig(path)
            written.append(path)

        return written

    def build(
        self,
        names: Sequence[str],
        outdir: Path | None = None,
        style_file: Path | None = None,
    ) -> None:
        """Build and save the named figures, in the order given."""
        self.apply_style(style_file)

        for name in names:
            fig = self.builders[name]()
            written = self.save_figure(name, fig, outdir)
            plt.close(fig)
            print(f"  {name}: " + ", ".join(p.name for p in written))

    def main(self, argv: Sequence[str] | None = None) -> None:
        """Command-line entry point for this collection."""
        parser = argparse.ArgumentParser(
            prog=self.name,
            description="Regenerate registered figures.",
        )
        parser.add_argument(
            "names",
            nargs="*",
            help="figures to build (default: none; use --all or --list)",
        )
        parser.add_argument("--all", action="store_true", help="build every figure")
        parser.add_argument(
            "--list", action="store_true", help="list registered figures and exit"
        )
        parser.add_argument(
            "--outdir",
            type=Path,
            default=self.outdir,
            help=f"output directory (default: {self.outdir.name}/)",
        )
        parser.add_argument(
            "--style",
            type=Path,
            default=self.style_file,
            help=f"Matplotlib style sheet (default: {self.style_file.name})",
        )
        args = parser.parse_args(argv)

        if not self.builders:
            parser.error(
                f"the registry is empty; run `python {self.name}` so the figure "
                "definitions are imported"
            )

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
                "unknown figure(s): "
                + ", ".join(unknown)
                + f"\nregistered: {', '.join(sorted(self.builders))}"
            )

        revision = git_revision(self.style_file.parent)
        print(f"Generating {len(names)} figure(s) at revision {revision}")
        self.build(names, args.outdir, args.style)
        print(f"Wrote {len(names) * len(self.formats)} file(s) to {args.outdir}")
