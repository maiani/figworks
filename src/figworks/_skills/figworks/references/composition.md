# Composition and optional producers

Read the relevant section when adding equations, scenes, circuits, or SVG.
The starter covers ordinary Matplotlib/grid composition.

## Share the project's style

```python
import matplotlib.pyplot as plt
from figworks import Figure, load_theme

theme = load_theme("style.md")
# Dimensions are caller choices, not a universal publication format.
figure = Figure("178mm", "80mm", theme=theme, background="white")
panel = figure.panel("response", "18mm", "10mm", "145mm", "52mm")
with plt.rc_context(theme.rc()):
    plot, ax = panel.subplots()
    ax.plot([0, 1, 2], [0, 1, 0])  # replace the illustrative data
    panel.add(plot, id="response-plot", fit="axes")
    plt.close(plot)
```

Use target dimensions supplied by the project; verify current official venue
requirements when submission compliance is requested. Avoid opaque source
backgrounds that hide neighbouring content. Closing a Matplotlib figure after
placement is safe because its SVG has already been imported.

Apply style settings before drawing. Pass a raw panel letter to `figure.label`
and let the theme format it; do not embed a journal's punctuation or font weight
in every call. Keep intentional exceptions explicit at the call site.

## TeX at its physical size

```python
import vectex

equation = vectex.render(r"$E = mc^2$", id_prefix="energy", **theme.vectex())
panel.add(equation, id="energy-equation", fit="none")
```

This assumes the `theme` and destination `panel` exist. Make room for the
rendered extent instead of shrinking every equation into a fixed box. VecTeX
uses `currentColor`; a semantic colour can be applied through
`figure.select("#energy-root").set_style(color=theme.color["ink"])`.

## Scenes, circuits, and anchored labels

Pass VecView scenes and VecWire circuits directly to `panel.add(source, id=...)`.
Use the installed producer's public API; no adapter belongs in the figure script.
The theme provides `vecview_text()`, `vecwire()`, and `vecwire_label()` settings.
Keep circuit and label units equal and check that the producer version supports
the supplied options.

For VecView, camera scale and source padding influence geometry relative to
screen-sized text and strokes. With content fitting, increasing camera scale
alone does not enlarge the final placement. Use `figure.fill_slot(slot_id,
equation)` for a label pinned to geometry that retains its physical size; its
reserved space may need adjustment after the scene is scaled.

`figure.fill_plane(plane_id, plot)` projects content into a scene plane. Match
the plane's aspect ratio to the source and check orientation and occlusion.
An upright label belongs in a slot. See the
[scene guide](https://github.com/maiani/figworks/blob/main/docs/usage/scenes-3d.md)
for complete examples and exact producer calls.

## Definitions, imports, and edits

`figure.define(svg.LinearGradient(id=..., elements=...))` returns `url(#id)` for
paint attributes. Use svg.py definitions with unique IDs, including their children.

Select by `#id`, `.class`, or tag; this is not a full CSS selector engine.
`set_attr` edits selected nodes; `set_style` can propagate a presentation change
through descendants. Check the scope before recolouring a compound object.

Free imported IDs survive; collisions gain a placement prefix and local
`href`/`url(#...)` references follow. Choose unique semantic IDs to avoid relying
on placement order. Imported root styling survives on a group, but stylesheet
selectors are not scoped or renamed. Prefer inline styles/presentation attributes.

`fill` consumes its target. Retain its returned group and assign a unique ID if
it must be addressed again. Generate subsequent exports from the revised script;
keep any requested manual SVG edits separately identifiable.
