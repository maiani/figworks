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
* `set_style(**style)` — merge inline CSS into each node's `style` attribute.
* `set_attr(name, value)` — set a raw attribute (underscores become hyphens).

Operations return the `Selection` so calls can be chained.

## Error handling

Selectors that are still unsupported (for example whitespace-separated
combinators) raise a clear `ValueError` rather than silently misbehaving.

```python
fig.select("panel > text")  # raises ValueError
```
