# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-05

### Changed

- **Renamed from FigForge to FigWorks.** The distribution and import name is
  now `figworks` (was `figforge`), because `figforge` on PyPI belongs to an
  unrelated project. The classes and ids written into the output change prefix
  from `figforge-` to `figworks-` (`figworks-arrowhead`, `figworks-label`,
  `data-figworks-placeholder`, …), and so do Matplotlib clip-path ids, which
  are salted with the package name.
- The circuit producer is now VecWire (`vecwire`, formerly cirquit):
  `examples/vecwire_panel.py` and `tests/test_vecwire.py`.
- Prose spells the suite FigWorks, VecTeX, VecView, and VecWire; code, package
  names, and commands stay lowercase.

## [0.1.0] - 2026-10-05

### Added

- Type information: the package ships `py.typed` and passes `mypy --strict`.
  Numeric attributes reach svg.py as `Decimal`s formatted like before, and
  string-built attributes (`transform`, `d`, `points`) are set on the element
  directly, so typing changed no output byte.
- `Figure.fill_slot(id, source)` fills an anchor group, such as a VecView
  `Scene.slot`, with content kept at its own physical size however the scene
  was scaled to fit its panel, aligned on the anchor by the group's
  `data-align`. Pinning a TeX label to a world point no longer needs an
  invisible reservation rectangle, a hand-computed scene-to-figure offset, or a
  panel sized to the scene at 1:1.
  Fragments from Vectex before 0.2 declare their size without a unit and come
  out at 3/4 size; use VecTeX 0.2 or later.
- VecWire circuit schematics place through `to_svg_document()` with no adapter,
  the third producer to do so. `tests/test_vecwire.py` covers placement, id and
  `data-component` survival, uniform scaling, export, and determinism, and
  skips when VecWire is absent. `examples/vecwire_panel.py` sets a shunted
  junction beside its potential.
- `fill_plane(id, source)`, which fills a group whose transform maps the unit
  square onto its target. Paired with vecview's `Scene.plane`, it puts a plot
  *in* a plane of a 3D scene rather than flat in its own panel.
- VecView scenes place through `to_svg_document()`, as an optional source.
- `FigureCollection`, and a thesis-scale example driving the Matplotlib bridge
  from a shared style sheet.
- `Figure`, `Panel`, anchors and grid layout; native text, labels, rectangles,
  lines and arrows; `#id`, `.class` and tag selectors; placeholders; the
  Matplotlib bridge; and SVG, PDF and PNG export.

### Changed

- Every example writes into `examples/out/` rather than the working directory.
- **Python 3.12 is now the floor**, raised from 3.10, matching the sibling
  projects. VecTeX already required 3.11, so the old floor could not resolve.
- Ruff checks an explicit rule set (`B, E, F, I, N, RUF, S, UP`), matching
  VecTeX and VecView, instead of whatever the installed ruff enables by
  default, which made `ruff check` fail or pass depending on the version.
- The `backends/` and `themes/` subpackages are flattened into `_export.py`,
  `matplotlib.py`, and a `Theme` dataclass in `figure.py`.

### Fixed

- `Figure.save(path, dpi=...)` rasterizes PNG at `dpi` whatever unit the figure
  size was given in. cairosvg applies `dpi` only to physical units, so a figure
  sized in px came out at one pixel per px regardless of the requested
  resolution.
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
