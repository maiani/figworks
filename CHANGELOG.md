# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Figure.grid` creates named panels with row and column ratios, rectangular
  spans, empty cells, and physical margins and gaps. Returned panels work with
  the existing placement, anchors, and Matplotlib API.
- `examples/transmon_figure.py`, the README figure: a transmon qubit in a
  Physical Review two-column figure, composing a VecView device with TeX labels
  pinned in 3D, a VecWire circuit, and two Matplotlib panels on one grid. It is
  the first example to place VecTeX output.
- `fit="none"` on `Figure.add` and `Panel.add` places a source at the physical
  size its document declares instead of scaling it to the panel, so a circuit
  or equation drawn with 8 pt text prints at 8 pt; larger content overhangs.
  `align` (`"center"`, `"north"`, `"northwest"`, …, the slot names) picks the
  point of the panel it sits on, and with the scaling fits places content in
  the room a kept aspect ratio leaves. The transmon example's circuit, scaled
  to 95 % before, is placed this way, and `vecwire_panel.py`'s, whose labels
  printed at 12 pt beside a plot shrunk to 6.6 pt text, now prints both at
  their drawn size: the circuit unscaled, the plot by its axes frame.
- Tests that place real VecTeX output -- ids, recolouring, a slot label's point
  size -- and a CI job that installs TeX to run them and the transmon example.
  FigWorks had no test of the one sibling it requires.

### Changed

- Use ty for type checking in development and CI instead of mypy.
- VecTeX 0.4 or newer is required; CI had been testing against 0.1.0. Since
  VecTeX 0.3 a label's glyphs use `currentColor`, so recolour a placed label
  with `color`, not `fill`, and size a VecView slot with its `width_px` and
  `height_px`.
- The README is written for the PyPI project page: install from PyPI, absolute
  links pinned to the release tag, and the transmon figure with the code that
  composes it.
- `examples/vecview_panel.py` loses its `background` argument, which only the
  README figure script used.

### Fixed

- `set_style` reaches what a source styled itself. Matplotlib writes a line's
  colour on its path and VecWire a symbol's on its strokes, and those win over
  a style set on the group a selector finds, so restyling a plotted line by its
  gid changed nothing. The property is now also replaced on every descendant
  that declares it, inline or as an attribute; a declared `none` is kept.
- The sdist ships `tests/conftest.py`; without it, tests run from the sdist
  were missing the fixtures they use.

## [0.7.0] - 2026-10-05

### Added

- **`style.md`: a publication's look as one document.** Its YAML frontmatter
  holds design tokens -- `font` (face and size scale), `line` (data, frame, and
  hairline weights), `color` (named by meaning), `cycle`, `marker`, `page`
  (named lengths such as column widths) -- and its Markdown body is the style
  guide. A style names a `base` (a built-in or another `style.md`) and states
  only its differences; `matplotlib` layers existing Matplotlib styles
  underneath and `rcparams` overrides anything last. `load_theme(path)` loads
  it; `Theme.rc()` generates validated Matplotlib settings, and `Theme.px()`
  hands lengths to producers that draw in px.
- Built-in styles following published journal figure guidelines: `nature`,
  `aps` (Physical Review), and `ieee`, beside `paper` and `presentation`, which
  are now `style.md` files themselves.
- A "Styles" documentation page.

### Changed

- `Figure(theme=...)`, `theme_rc(...)`, and `FigureCollection(style=...)` accept
  a built-in name, a `style.md` path, or a `Theme`. `theme_rc` now generates the
  full settings a style implies (sizes, weights, colours), not only fonts.
- `Theme` is the loaded form of a style; it is no longer constructed directly.
- `FigureCollection` takes one `style` argument, replacing `theme` and
  `style_file`; a style can layer a `.mplstyle` with its `matplotlib` key.
- PyYAML is a runtime dependency, to read `style.md` frontmatter.
- The thesis example's look is `examples/thesis_style.md`, built on `aps`.

## [0.6.0] - 2026-10-05

### Changed

- **`FigureCollection` is reworked.** A builder may return a FigWorks `Figure`,
  which is now saved as a vector figure with `Figure.save`; the example used to
  rasterize composed figures through a PNG so the collection could save them as
  Matplotlib figures. Matplotlib figures are saved deterministically (pinned SVG
  ids, no creation dates) after a font check. Each build applies Matplotlib's
  defaults, then the optional style sheet, then the theme's typeface and size,
  and restores the previous settings afterwards. The constructor takes `outdir`,
  `theme`, `style_file` (now optional), `formats`, and `dpi`; `name` is gone
  (the program name comes from the command line) and `--style` with it. `build`
  returns the paths it wrote.

### Added

- `figworks.matplotlib.save_figure(fig, path, dpi=...)`: write a Matplotlib
  figure byte-identically, after checking its fonts.
- A "Figure collections" documentation page, and tests for the collection.

### Fixed

- `set_style` reaches what a source styled itself. Matplotlib writes a line's
  colour on its path and VecWire a symbol's on its strokes, and those win over
  a style set on the group a selector finds, so restyling a plotted line by its
  gid changed nothing. The property is now also replaced on every descendant
  that declares it, inline or as an attribute; a declared `none` is kept.
- Importing FigWorks no longer switches Matplotlib to the Agg backend, which
  silently disabled interactive plotting in notebooks. Only the collection's
  command-line entry point selects it.
- PDF output is byte-identical across runs: cairo's creation date is omitted.

## [0.5.0] - 2026-10-05

### Added

- `Panel.subplots(nrows, ncols, **kwargs)`: a Matplotlib figure exactly the
  panel's physical size, whose axes grid fills it edge to edge, so the panel is
  the axes frame and tick labels fall outside it.
- `fit="axes"` for `Panel.add` and `Figure.add`: place a Matplotlib figure by its
  axes frame (the union of its axes) rather than its drawn content, with labels
  hanging outside. With `Panel.subplots` the plot lands at exactly 1:1, so text
  keeps its nominal size and frames in a row line up whatever their tick labels.
  `fit="content"` remains the default.
- `figworks.matplotlib.axes_frame(fig)`.

### Changed

- `examples/two_panel_figure.py` shows two aligned panels with very different
  tick labels.

## [0.4.0] - 2026-10-05

### Added

- `Figure.save` checks fonts before rendering PDF or PNG, and raises
  `figworks.fonts.FontError` instead of letting fontconfig substitute silently.
  For each run of text it resolves the first family of its `font-family` (the
  only one CairoSVG honours) in the run's weight and style, verifies the chosen
  file's real family, and checks that every character has a glyph. A generic
  family is reported too. The check reads the matched file with `fc-query`, so
  a stale fontconfig cache that echoes the requested family back is caught.
- `figworks.matplotlib.theme_rc(theme)`: Matplotlib settings for the theme's
  typeface and size, math text included.

### Changed

- The default theme typeface is TeX Gyre Heros (was Arial), a free Helvetica
  clone available with TeX Live and as `fonts-texgyre`. The figure root carries
  it as `font-family`, so sources that name no font inherit it.
- The examples set their plots in the theme typeface, and the VecWire example
  labels its junction `JJ`: TeX Gyre Heros has no subscript `ⱼ`.

## [0.3.0] - 2026-10-05

### Added

- A "Units & sizes" page: how the canvas, each source's declared size, every
  placement operation, and export handle units, which operations honour a
  source's physical size (only `fill_slot`), how to place a VecView scene at
  exactly 1:1, and what a new producer should declare.

### Fixed

- `set_style` reaches what a source styled itself. Matplotlib writes a line's
  colour on its path and VecWire a symbol's on its strokes, and those win over
  a style set on the group a selector finds, so restyling a plotted line by its
  gid changed nothing. The property is now also replaced on every descendant
  that declares it, inline or as an attribute; a declared `none` is kept.
- Imported ids are unique across sources. A colliding id is prefixed with the
  placement id (or the slot, plane, or placeholder it fills) and its `url(#…)`
  and `href` references follow; an identical colliding definition is shared
  instead. Two scenes with a `glow` gradient no longer silently share the first
  one's colour, and two circuits with the same node names stay separately
  selectable. Free ids are kept, so selection by id works as before. Reusing a
  placement id now raises `ValueError`.

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

- `set_style` reaches what a source styled itself. Matplotlib writes a line's
  colour on its path and VecWire a symbol's on its strokes, and those win over
  a style set on the group a selector finds, so restyling a plotted line by its
  gid changed nothing. The property is now also replaced on every descendant
  that declares it, inline or as an attribute; a declared `none` is kept.
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
