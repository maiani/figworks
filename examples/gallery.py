"""Build FigWorks' gallery and audit exactly the figures just generated.

Each gallery figure is a self-contained script in this directory. This builder
runs them, checks every SVG with the publication preflight, and records hashes
and findings in ``examples/out/gallery-report.json``. With ``--docs`` it also
refreshes the previews and pages of the documentation gallery.

Usage:
    python examples/gallery.py                     # build and audit everything
    python examples/gallery.py --only graphene_bands
    python examples/gallery.py --docs              # also refresh docs/gallery

Every figure needs VecView and a TeX installation; the transmon also needs
VecWire. A missing producer fails the build; nothing is skipped silently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from lxml import etree

from figworks import Figure
from figworks.preflight import check_document

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "out"
DOCS = ROOT / "docs" / "gallery"
IMAGES = ROOT / "docs" / "images"
SOURCE = "https://github.com/maiani/figworks/blob/main/examples"


@dataclass(frozen=True)
class Example:
    name: str
    field: str
    title: str
    description: str
    shows: str
    requires: str = "VecView and TeX"


EXAMPLES = (
    Example(
        "transmon_figure",
        "Superconducting qubits",
        "A transmon, from device to spectrum",
        "The device, its circuit and Hamiltonian, the cosine potential with its "
        "lowest levels, and the charge dispersion that vanishes as E_J/E_C grows.",
        "All four producers in one figure: a VecView device, a VecWire circuit, "
        "VecTeX labels pinned into both, and Matplotlib panels aligned on the grid.",
        "VecView, VecWire, and TeX",
    ),
    Example(
        "graphene_bands",
        "Condensed matter",
        "Dirac electrons in graphene",
        "The honeycomb lattice, its two tight-binding bands touching at the Dirac "
        "points, the band structure along high-symmetry lines, and the density of states.",
        "Two VecView scenes, a lattice and a band surface, beside Matplotlib panels "
        "that share the energy axis.",
    ),
    Example(
        "microring_resonator",
        "Photonics",
        "A microring resonator",
        "A ring coupled to a bus waveguide, its comb of resonances, and how the "
        "coupling regime shapes each dip.",
        "A VecView chip built from extruded outlines, with colours that carry "
        "from the device into the spectra.",
    ),
    Example(
        "optical_tweezers",
        "Biophysics",
        "Stretching DNA with optical tweezers",
        "A DNA molecule held between two trapped beads, its worm-like-chain "
        "force-extension curve, and the Brownian motion that calibrates the trap.",
        "Spheres, cones, and a helix in VecView beside simulated measurements "
        "and fits in Matplotlib.",
    ),
    Example(
        "hodgkin_huxley",
        "Neuroscience",
        "The action potential",
        "Sodium and potassium channels in the membrane, and the Hodgkin-Huxley "
        "model's spikes, conductances, and firing threshold.",
        "A membrane patch in VecView whose ion colours return in every trace.",
    ),
    Example(
        "exoplanet_transit",
        "Astrophysics",
        "A transiting hot Jupiter",
        "The transit geometry, a limb-darkened light curve with residuals, and "
        "the planet's transmission spectrum.",
        "A VecView star system with pinned VecTeX labels beside stacked, "
        "aligned Matplotlib panels.",
    ),
    Example(
        "energy_landscape",
        "Chemistry",
        "Reaction paths on a potential-energy surface",
        "The Müller-Brown surface in 3D, its minimum-energy path, and the barriers "
        "along the reaction coordinate.",
        "A Matplotlib contour map rendered into a plane of a VecView scene with "
        "`fill_plane`, under the surface it maps.",
    ),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preview(example: Example) -> None:
    """Give the preview a white page, so it reads in either site theme, without rescaling it."""
    source = OUT / f"{example.name}.svg"
    root = etree.parse(str(source)).getroot()
    page = Figure(root.get("width"), root.get("height"))
    page.rect(x=0, y=0, width=page.width, height=page.height, fill="white", stroke="none")
    page.panel("preview", 0, 0, page.width, page.height).add(
        source, id="artwork", fit="none", align="northwest"
    )
    page.save(IMAGES / f"gallery-{example.name}.svg")


def detail_page(example: Example, record: dict) -> str:
    counts = Counter(issue["code"] for issue in record["issues"])
    findings = "\n".join(f"- `{code}`: {count}" for code, count in sorted(counts.items()))
    limits = "\n".join(f"- {limit}" for limit in record["unchecked"])
    image = f"../images/gallery-{example.name}.svg"
    return (
        f"# {example.title}\n\n"
        f"*{example.field}.* {example.description}\n\n"
        f"![{example.title}]({image})\n\n"
        f"**What it shows of FigWorks.** {example.shows}\n\n"
        f"**Requires** {example.requires}.\n\n"
        f"```bash\npython examples/{example.name}.py\n```\n\n"
        f"[Python source]({SOURCE}/{example.name}.py) · [SVG]({image})\n\n"
        "## Preflight\n\n"
        "Recorded by `python examples/gallery.py`; findings are for review, "
        "not a certification.\n\n"
        f"{findings or 'No findings.'}\n\n"
        f"Not checked:\n\n{limits}\n"
    )


def index_page() -> str:
    cards = "\n\n".join(
        f"-   **[{item.title}]({item.name}.md)**\n\n"
        f"    [![{item.title}](../images/gallery-{item.name}.svg)]({item.name}.md)\n\n"
        f"    *{item.field}.* {item.description}"
        for item in EXAMPLES
    )
    return (
        "# Gallery\n\n"
        "Figures from across the sciences, each built by one self-contained script "
        "at its printed size: 183 mm wide, the two-column width of Nature. "
        "Every one pairs a schematic with quantitative panels computed from the "
        "model it illustrates, and every element of the SVG stays editable.\n\n"
        "Data shown as measurements are simulated, with fixed seeds; each script "
        "says which.\n\n"
        f'<div class="grid cards" markdown>\n\n{cards}\n\n</div>\n\n'
        "## Rebuild\n\n"
        "```bash\n"
        "python examples/gallery.py         # build and audit every figure\n"
        "python examples/gallery.py --docs  # also refresh these pages\n"
        "```\n\n"
        "The build needs VecView, VecWire, and TeX, and fails rather than skip a "
        "figure. It records each SVG's hash and preflight findings in "
        "`examples/out/gallery-report.json`.\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=[item.name for item in EXAMPLES])
    parser.add_argument("--docs", action="store_true", help="refresh the documentation gallery")
    args = parser.parse_args()
    if args.docs and args.only:
        parser.error("--docs requires a full build; omit --only")
    selected = [item for item in EXAMPLES if not args.only or item.name in args.only]
    OUT.mkdir(exist_ok=True)
    report = {"complete": False, "selection": [item.name for item in selected], "examples": []}
    report_path = OUT / "gallery-report.json"
    # Replace a previous success at once: an interrupted run must not look complete.
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    errors = 0
    for example in selected:
        script = ROOT / "examples" / f"{example.name}.py"
        svg = OUT / f"{example.name}.svg"
        before = svg.stat().st_mtime_ns if svg.exists() else None
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
        if not svg.is_file() or svg.stat().st_mtime_ns == before:
            raise RuntimeError(f"{script.name} did not regenerate {svg}")
        result = check_document(etree.parse(str(svg)).getroot())
        errors += sum(issue.severity == "error" for issue in result.issues)
        print(f"{example.name}: {result.summary()}", flush=True)
        record = {
            "example": example.name,
            "artifact": svg.relative_to(ROOT).as_posix(),
            "source_sha256": digest(script),
            "svg_sha256": digest(svg),
            "issues": [asdict(issue) for issue in result.issues],
            "unchecked": list(result.unchecked),
        }
        report["examples"].append(record)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.docs:
            preview(example)
            DOCS.mkdir(exist_ok=True)
            (DOCS / f"{example.name}.md").write_text(detail_page(example, record), encoding="utf-8")
    if args.docs:
        (DOCS / "index.md").write_text(index_page(), encoding="utf-8")
    report["complete"] = True
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(f"{errors} preflight errors; inspect {report_path}")


if __name__ == "__main__":
    main()
