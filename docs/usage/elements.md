# Native SVG elements

FigWorks constructs SVG elements through lightweight factories and appends
them to the document as editable `lxml` nodes. All factories accept `id=`,
`class_=`, and additional SVG attributes; underscores in keyword arguments are
converted to hyphens.

## Shapes

```python
from figworks.elements import circle, ellipse, line, path, polyline, rect

line(x1=0, y1=0, x2=10, y2=10)
rect(x=0, y=0, width=20, height=10)
circle(cx=5, cy=5, r=2)
ellipse(cx=5, cy=5, rx=3, ry=2)
polyline([(0, 0), (5, 5), (10, 0)])
path("M 0 0 L 10 10")
```

## Text

Multi-line strings are split into `<tspan>` runs automatically.

```python
from figworks.elements.text import text_element

text_element("Line one\nLine two", x=10, y=20, font_size="8pt")
```

## Arrows

```python
from figworks.elements.arrows import line_arrow, ensure_arrow_marker

ensure_arrow_marker(document)
line_arrow(0, 0, 10, 10, stroke="black")
```

The arrowhead marker is defined once in the document's `<defs>` and shared by
all arrows.

## Adding through the figure

The same elements can be added through `Figure` convenience methods, which
wire up the theme automatically:

```python
fig.rect(x=5, y=5, width=20, height=10, id="box")
fig.circle(cx=5, cy=5, r=2, fill="red")
```
