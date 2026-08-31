# AGENTS.md

Guidance for coding agents working on FigForge.

## Project Intent

FigForge is an SVG-first Python package for assembling publication-quality scientific figures from Matplotlib plots, Vectex equations, vecview 3D scenes, native SVG elements, annotations, and semantic figure objects.

Keep the package deterministic, small, and easy to inspect. The main design goal is semantic editability through stable IDs, classes, panels, and roles.

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
  Vectex and vecview both work this way, with no adapter in FigForge and no import
  in either direction. Do not add an adapter, base class, or registry for a new
  source until that contract is demonstrably insufficient.
- Keep optional sources optional: their tests must use `pytest.importorskip`, and
  they must not appear in `dependencies`. vecview in particular is unpublished, so
  a dependency entry would resolve to an unrelated PyPI package.
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

Validation:

```bash
pytest
ruff check .
```

Examples:

```bash
python examples/minimal_svg.py
python examples/matplotlib_panel.py
python examples/two_panel_figure.py
python examples/vecview_panel.py         # requires vecview from a checkout
python examples/vecview_plane_plot.py    # a plot projected onto a plane in 3D
```

## Code Style

- Keep public APIs narrow and documented through examples.
- Add tests for behavior, not implementation details.
- Prefer clear errors for unsupported selectors, units, or export formats.
- Preserve user-authored files and unrelated changes.
- Keep comments short and only where they clarify non-obvious behavior.
