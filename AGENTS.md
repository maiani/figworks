# AGENTS.md

Guidance for coding agents working on FigWorks.

## Project Intent

FigWorks is an SVG-first Python package for assembling publication-quality scientific figures from Matplotlib plots, VecTeX equations, VecView 3D scenes, VecWire circuit schematics, native SVG elements, annotations, and semantic figure objects.

Keep the package deterministic, small, and easy to inspect. The main design goal is semantic editability through stable IDs, classes, panels, and roles.

## The Suite

FigWorks is the composition layer of four projects developed together:

| Project | Produces |
| --- | --- |
| **FigWorks** | composed, exported multi-panel figures |
| [VecTeX](https://github.com/maiani/vectex) | editable TeX equations as SVG fragments |
| [VecView](https://github.com/maiani/vecview) | layered 3D schematics as SVG documents |
| VecWire | editable circuit schematics as SVG documents |

**Naming.** In prose the projects are FigWorks, VecTeX, VecView, and VecWire.
Distribution names, import names, commands, and file paths are lowercase
(`figworks`, `vectex`, `vecview`, `vecwire`), and so is anything inside code
spans. FigWorks was FigForge and VecWire was cirquit until both PyPI names
turned out to be taken.

Why they are separate projects, and why that matters for what you may change
here:

**One target.** A publication figure should be generated from code *and* remain
editable afterwards. All four emit vector SVG with stable ids and deterministic,
byte-identical output, so a figure can be regenerated, diffed in version control,
and still opened in Inkscape to nudge a label. Anything that makes output
non-deterministic or ids unstable breaks the shared premise, not just this
package.

**One contract.** FigWorks coordinates maintained tools instead of reproducing
them: Matplotlib already plots, TeX already typesets. The entire integration
surface is an object exposing `to_svg_document()`.

**Co-development is what tests the contract.** A one-method interface is easy to
claim and hard to trust. VecTeX, VecView, and VecWire share no code -- a TeX
compiler, a 3D projector, and a circuit drawer -- and all three integrate through
that method alone, with no adapter here and no import in either direction. That
is the evidence the contract is sufficient, and the standing reason to refuse base
classes, registries, and plugin systems aimed at hypothetical future sources.
VecWire was a third producer and a chance to falsify the contract; it integrated
without an adapter, which is further evidence, not proof. Every new producer is
another such test: if one genuinely cannot be served by `to_svg_document()`, that
is a real finding and a design conversation, not a licence to add an adapter
quietly.

The dependency edges are deliberately uneven: VecTeX is a runtime requirement,
VecView and VecWire are optional and installed from a checkout, and none depends
on FigWorks. Do not make that symmetric for tidiness.

## Current Scope

Focus on the MVP described in `PLAN.md`:

- `Figure(width, height, theme="paper")`, where a theme is a built-in or a `style.md`
- `Figure.panel(id, x, y, w, h)`
- `Panel.add(source, id=...)`
- native text, labels, rectangles, lines, and arrows
- selectors for `#id`, `.class`, and SVG tag names
- `.svg`, `.pdf`, and `.png` export
- examples and pytest coverage

Do not implement the declarative YAML layer, GUI, CLI polish, advanced path geometry, or a full CSS selector engine until the core API is stable.

## Engineering Constraints

- Use the `src/` layout.
- Keep runtime dependencies limited to the planned core set unless `PLAN.md` is updated first.
- Use `svg.py` for constructing native SVG elements wherever possible.
- Integrate SVG-producing libraries through the `to_svg_document()` protocol only.
  Do not add an adapter, base class, or registry for a new source until that
  contract is demonstrably insufficient -- see **The Suite** for why that bar is
  set where it is.
- Keep optional sources optional: their tests must use `pytest.importorskip`, and
  they must not appear in `dependencies`. VecView and VecWire in particular are
  unpublished, so a dependency entry would not resolve.
- Keep `lxml` focused on mutable DOM operations: parsing imported SVG, selection, deletion, style edits, and final serialization.
- Use Matplotlib for plot generation and SVG export.
- Use CairoSVG for PDF and PNG export.
- Prefer stable IDs and readable generated SVG.
- The document root carries a px `viewBox` matching its physical `width`/`height`.
  Elements are placed in px user units, so removing it silently breaks every
  export above 96 DPI. See `tests/test_document.py`.
- `SVGDocument.append` must test `parent is None`, not truthiness: an lxml element
  with no children is falsy, so `parent or self.root` silently retargets the root
  and drops content into the wrong place. `fill_plane` passes an empty group.
- Avoid broad abstractions until duplication or complexity justifies them.

## Commands

Recommended local setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Validation (all must pass before reporting a change complete):

```bash
ruff format --check .
ruff check .
mypy
pytest
```

Rendering tests and examples need TeX Gyre Heros and DejaVu Sans installed and
fontconfig's `fc-match`/`fc-query` on `PATH` (Debian/Ubuntu: `fonts-texgyre
fonts-dejavu-core fontconfig`): PDF and PNG export refuse to substitute a missing
font. Unit tests of the check itself use a fake resolver.

The package is typed (`py.typed`, `mypy --strict` over `src`). svg.py writes
floats with `repr`, so numeric attributes go through `px_decimal` to keep the
`%g` formatting; attributes FigWorks builds as strings (`transform`, `d`,
`points`) are passed to `svg_to_lxml(..., raw=...)` rather than cast.

Examples:

```bash
python examples/minimal_svg.py
python examples/matplotlib_panel.py
python examples/two_panel_figure.py
python examples/vecview_panel.py         # requires vecview from a checkout
python examples/vecview_plane_plot.py    # a plot projected onto a plane in 3D
python examples/vecwire_panel.py         # requires vecwire from a checkout
```

## Code Style

- Keep public APIs narrow and documented through examples.
- Add tests for behavior, not implementation details.
- Prefer clear errors for unsupported selectors, units, or export formats.
- Preserve user-authored files and unrelated changes.
- Keep comments short and only where they clarify non-obvious behavior.
