# AGENTS.md

Guidance for coding agents working on FigForge.

## Project Intent

FigForge is an SVG-first Python package for assembling publication-quality scientific figures from Matplotlib plots, Vectex equations, vecview 3D scenes, cirquit circuit schematics, native SVG elements, annotations, and semantic figure objects.

Keep the package deterministic, small, and easy to inspect. The main design goal is semantic editability through stable IDs, classes, panels, and roles.

## The Suite

FigForge is the composition layer of four projects developed together:

| Project | Produces |
| --- | --- |
| **FigForge** | composed, exported multi-panel figures |
| [Vectex](https://github.com/maiani/vectex) | editable TeX equations as SVG fragments |
| [vecview](https://github.com/maiani/vecview) | layered 3D schematics as SVG documents |
| cirquit | editable circuit schematics as SVG documents |

Why they are separate projects, and why that matters for what you may change
here:

**One target.** A publication figure should be generated from code *and* remain
editable afterwards. All four emit vector SVG with stable ids and deterministic,
byte-identical output, so a figure can be regenerated, diffed in version control,
and still opened in Inkscape to nudge a label. Anything that makes output
non-deterministic or ids unstable breaks the shared premise, not just this
package.

**One contract.** FigForge coordinates maintained tools instead of reproducing
them: Matplotlib already plots, TeX already typesets. The entire integration
surface is an object exposing `to_svg_document()`.

**Co-development is what tests the contract.** A one-method interface is easy to
claim and hard to trust. Vectex, vecview, and cirquit share no code -- a TeX
compiler, a 3D projector, and a circuit drawer -- and all three integrate through
that method alone, with no adapter here and no import in either direction. That
is the evidence the contract is sufficient, and the standing reason to refuse base
classes, registries, and plugin systems aimed at hypothetical future sources.
cirquit was a third producer and a chance to falsify the contract; it integrated
without an adapter, which is further evidence, not proof. Every new producer is
another such test: if one genuinely cannot be served by `to_svg_document()`, that
is a real finding and a design conversation, not a licence to add an adapter
quietly.

The dependency edges are deliberately uneven: Vectex is a runtime requirement,
vecview and cirquit are optional and installed from a checkout, and none depends
on FigForge. Do not make that symmetric for tidiness.

## Current Scope

Focus on the MVP described in `PLAN.md`:

- `Figure(width, height, theme="paper")`
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
  they must not appear in `dependencies`. vecview and cirquit in particular are
  unpublished, and the name `cirquit` on PyPI belongs to an unrelated package, so a
  dependency entry would install the wrong thing.
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

The package is typed (`py.typed`, `mypy --strict` over `src`). svg.py writes
floats with `repr`, so numeric attributes go through `px_decimal` to keep the
`%g` formatting; attributes FigForge builds as strings (`transform`, `d`,
`points`) are passed to `svg_to_lxml(..., raw=...)` rather than cast.

Examples:

```bash
python examples/minimal_svg.py
python examples/matplotlib_panel.py
python examples/two_panel_figure.py
python examples/vecview_panel.py         # requires vecview from a checkout
python examples/vecview_plane_plot.py    # a plot projected onto a plane in 3D
python examples/cirquit_panel.py         # requires cirquit from a checkout
```

## Code Style

- Keep public APIs narrow and documented through examples.
- Add tests for behavior, not implementation details.
- Prefer clear errors for unsupported selectors, units, or export formats.
- Preserve user-authored files and unrelated changes.
- Keep comments short and only where they clarify non-obvious behavior.
