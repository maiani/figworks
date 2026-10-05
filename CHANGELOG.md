# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- cirquit circuit schematics place through `to_svg_document()` with no adapter,
  the third producer to do so. `tests/test_cirquit.py` covers placement, id and
  `data-component` survival, uniform scaling, export, and determinism, and
  skips when cirquit is absent. `examples/cirquit_panel.py` sets a shunted
  junction beside its potential.
- `fill_plane(id, source)`, which fills a group whose transform maps the unit
  square onto its target. Paired with vecview's `Scene.plane`, it puts a plot
  *in* a plane of a 3D scene rather than flat in its own panel.
- vecview scenes place through `to_svg_document()`, as an optional source.
- `FigureCollection`, and a thesis-scale example driving the Matplotlib bridge
  from a shared style sheet.
- `Figure`, `Panel`, anchors and grid layout; native text, labels, rectangles,
  lines and arrows; `#id`, `.class` and tag selectors; placeholders; the
  Matplotlib bridge; and SVG, PDF and PNG export.

### Changed

- **Python 3.12 is now the floor**, raised from 3.10, matching the sibling
  projects. Vectex already required 3.11, so the old floor could not resolve.
- Ruff checks an explicit rule set (`B, E, F, I, N, RUF, S, UP`), matching
  Vectex and vecview, instead of whatever the installed ruff enables by
  default, which made `ruff check` fail or pass depending on the version.
- The `backends/` and `themes/` subpackages are flattened into `_export.py`,
  `matplotlib.py`, and a `Theme` dataclass in `figure.py`.

### Fixed

- Matplotlib panels are byte-identical from run to run. Matplotlib salts its
  clip-path and marker ids with a fresh random value per export and stamps the
  export date, so every figure containing a plot changed on each regeneration.
  The export now pins `svg.hashsalt` and drops the `Date` metadata.
- The document root carries a px `viewBox` matching its physical size. Without
  it, every export above 96 DPI put its content in a corner at the wrong scale.
- `SVGDocument.append` no longer retargets the root when given an empty group
  as parent: an lxml element with no children is falsy.

### Known limitations

- Imported ids, including `<defs>` children, are copied verbatim. Two sources
  that share an id collide, and `url(#…)` or `#id` resolves to the first.
