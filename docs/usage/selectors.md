# Selectors

Every element in the document can be addressed by a stable identifier. FigWorks
provides a small, predictable selector engine returning a `Selection` object.

## Selecting

```python
fig.select("#some-id")  # by id
fig.select(".some-class")  # by class
fig.select("text")  # by SVG tag name
```

A `Selection` is iterable and sized:

```python
sel = fig.select("rect")
len(sel)
for node in sel:
    ...
```

## Mutating a selection

```python
fig.select("#gap-arrow").delete()
fig.select(".axis-label").set_style(font_size="8pt", fill="red")
fig.select("text").set_attr("font-family", "Arial")
```

* `delete()` — remove every selected node from the document.
* `set_style(**style)` — merge inline CSS into each node's `style` attribute,
  and replace the same properties wherever a descendant declares them.
* `set_attr(name, value)` — set a raw attribute (underscores become hyphens).

Operations return the `Selection` so calls can be chained.

### Restyling placed content

Sources style their leaves directly: Matplotlib writes a line's colour on its
path, VecWire a symbol's on each stroke. A leaf's own declaration wins over
anything inherited, so styling only the selected group would change nothing
visible. `set_style` therefore also replaces the property on every descendant
that declares it, inline or as a presentation attribute:

```python
line.set_gid("phase-curve")  # in the plotting code
...
fig.select("#phase-curve").set_style(stroke="#c2185b")  # the line, and its markers
```

A descendant's `none` is kept, so recolouring a line with `fill` does not fill
it, and a symbol's unfilled parts stay unfilled. Descendants that declare
nothing inherit the new value as before. To change one attribute on the
selected nodes only, use `set_attr`.

## Ids across sources

Every id in a figure is unique, even when sources reuse names. Placing a source
keeps its ids unless one is already taken:

- **Free ids are kept**, so an id given while building a scene, a circuit, or a
  plot stays selectable after placement.
- **A colliding id is prefixed with the placement id**: placing two circuits as
  `lc1` and `lc2`, both with an inductor `L`, gives `#L` and `#lc2-L`. Content
  filled into a slot, plane, or placeholder takes that target's id as its
  prefix. If the prefixed name is taken too, a `-2`, `-3`, … suffix follows.
- **References follow the rename**: `url(#…)` in any attribute or style, and
  `href`/`xlink:href`, so the second source keeps its own gradient.
- **Identical definitions are shared**: a colliding `<defs>` entry that matches
  the existing one exactly is dropped and both sources use it. Matplotlib
  content-hashes its marker and clip-path ids, so identical plots share them.

The first source to claim an id keeps it, so the names depend on placement
order, which a script fixes. Reusing a *placement* id raises `ValueError`.

## Error handling

Selectors that are still unsupported (for example whitespace-separated
combinators) raise a clear `ValueError` rather than silently misbehaving.

```python
fig.select("panel > text")  # raises ValueError
```
