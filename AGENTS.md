# AGENTS.md

Guidance for coding agents working on FigForge.

## Project Intent

FigForge is an SVG-first Python package for assembling publication-quality scientific figures from Matplotlib plots, native SVG elements, annotations, and semantic figure objects.

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
- Keep `lxml` focused on mutable DOM operations: parsing imported SVG, selection, deletion, style edits, and final serialization.
- Use Matplotlib for plot generation and SVG export.
- Use CairoSVG for PDF and PNG export.
- Prefer stable IDs and readable generated SVG.
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
```

## Code Style

- Keep public APIs narrow and documented through examples.
- Add tests for behavior, not implementation details.
- Prefer clear errors for unsupported selectors, units, or export formats.
- Preserve user-authored files and unrelated changes.
- Keep comments short and only where they clarify non-obvious behavior.
