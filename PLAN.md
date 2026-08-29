# FigForge direction

FigForge is a thin, SVG-first composition layer for scientific figures. It
coordinates maintained tools instead of reproducing them:

- `svg.py` constructs native annotations and shapes.
- Matplotlib produces scientific plots as vector SVG.
- Vectex produces editable TeX equations as vector SVG.
- `lxml` handles selection and document assembly.
- CairoSVG exports the assembled SVG to PDF and PNG.

The canonical public operation is placement: `Figure.add(...)` and
`Panel.add(...)` accept an SVG string/path, a Matplotlib figure, or any object
whose `to_svg_document()` method returns a complete SVG document. Placeholder
replacement remains available for post-processing an existing SVG by semantic
ID; it is not a second composition model.

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
- Test fitting for non-zero viewBox origins and nested definitions.
- Document the difference between direct placement and gid replacement.
- Avoid expanding selector syntax until real editing workflows require it.

## Non-goals

FigForge is not a plotting library, TeX compiler, SVG path editor, GUI, scene
renderer, or declarative workflow engine. Those responsibilities belong to its
inputs and backends.
