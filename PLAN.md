# FigForge direction

FigForge is a thin, SVG-first composition layer for scientific figures. It
coordinates maintained tools instead of reproducing them:

- `svg.py` constructs native annotations and shapes.
- Matplotlib produces scientific plots as vector SVG.
- Vectex produces editable TeX equations as vector SVG.
- vecview produces layered 3D schematics as vector SVG.
- cirquit produces editable circuit schematics as vector SVG.
- `lxml` handles selection and document assembly.
- CairoSVG exports the assembled SVG to PDF and PNG.

The canonical public operation is placement: `Figure.add(...)` and
`Panel.add(...)` accept an SVG string/path, a Matplotlib figure, or any object
whose `to_svg_document()` method returns a complete SVG document. Vectex,
vecview, and cirquit all integrate through that protocol alone, with no adapter in FigForge
and no import in either direction -- the evidence that the contract is
sufficient, and the reason not to generalize it further. Placeholder
replacement remains available for post-processing an existing SVG by semantic
ID; it is not a second composition model.

For a Matplotlib figure with one or more SVG replacements, package-level
`compose(...)` is the primary interface. It maps axes directly to SVG sources
and does not require the higher-level `Figure` composition model or manual
placeholders.

## Scope

Keep the core limited to:

1. physical canvas and panel geometry;
2. generic SVG placement and fitting;
3. stable IDs and minimal selection/editing;
4. native labels, shapes, and arrows;
5. Matplotlib SVG export and gid replacement;
6. SVG, PDF, and PNG output.

Do not add backend base classes, registries, plugin systems, schemas, or wrapper
objects until two concrete implementations need the same behavior. A future
Plotly or Blender integration should first be a converter that produces a full
SVG document accepted by `add`. Only introduce a new abstraction when that
contract is insufficient in a demonstrated workflow.

## Near-term release work

- Exercise Matplotlib and Vectex together in publication-scale examples.
- Keep generated SVG IDs deterministic and collision-free.
- Namespace ids when importing SVG. Definitions are currently hoisted into the
  figure's `<defs>` verbatim, so two sources sharing a def id collide silently
  and the second takes the first's gradient. Pinned by
  `tests/test_vecview.py::test_duplicate_def_ids_across_scenes_collide`.
- Test fitting for non-zero viewBox origins and nested definitions. vecview
  scenes exercise the non-zero-origin path, since a fitted viewBox is centred
  on its content.
- Document the difference between direct placement and gid replacement.
- Avoid expanding selector syntax until real editing workflows require it.

## Recently added

- `fill_plane(id, source)` places content in a group whose transform maps the unit
  square onto its target, which is how a vecview scene plane receives a plot. The
  normalization is non-uniform by construction, so the target rectangle must match
  the content's aspect ratio.

## Non-goals

FigForge is not a plotting library, TeX compiler, SVG path editor, GUI, scene
renderer, 3D projection layer, or declarative workflow engine. Those responsibilities belong to its
inputs and backends.
