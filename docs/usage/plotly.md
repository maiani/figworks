# Plotly integration

Install the optional exporter:

```bash
pip install "figworks[plotly]"
plotly_get_chrome  # if Chrome or Chromium is not already installed
```

Plotly and Kaleido are optional; importing FigWorks does not import them.
Kaleido uses a local Chrome/Chromium process to render static images. See
[Plotly's export documentation](https://plotly.com/python/static-image-export/)
for browser discovery and setup.

```python
import plotly.graph_objects as go

from figworks import Figure
from figworks.plotly import plotly_to_svg

plot = go.Figure(go.Scatter(x=[0, 1, 2], y=[0, 1, 0], mode="lines+markers"))
plot.update_layout(font_family="DejaVu Sans", template="simple_white")

figure = Figure("160mm", "100mm")
panel = figure.panel("main", "10mm", "10mm", "140mm", "80mm")
panel.add(plotly_to_svg(plot, width=560, height=320), id="signal")
figure.save("signal.svg")
figure.save("signal.pdf")
figure.save("signal.png")
```

`plotly_to_svg(figure, *, width=None, height=None)` accepts a Plotly figure or
figure dictionary and returns a complete SVG string. Width and height are
positive integer CSS pixels; omit them to use Plotly's layout/export defaults.
The converter fixes export scale at 1 and leaves the input and global defaults
unchanged. Apply `plot.update_layout(template=theme.plotly())` to use a loaded FigWorks
theme. Explicit Plotly settings override the template; configure margins and
other plot-specific styling on the Plotly figure.

The returned SVG works wherever an SVG string is accepted, including `add`,
`fill`, and Matplotlib `compose` replacements. Use `fit="none"` to keep its
physical size (96 pixels per inch); ordinary placement scales the entire
export including labels. `fit="axes"` is specific to Matplotlib.

The converter normalizes generated ids and random trace classes, and rewrites
local references, so repeat exports can be byte-identical in the same renderer
environment. IDs are based on document order; editing a plot's structure can
change them. Give placements meaningful ids, such as `signal`, for subsequent
selection. FigWorks resolves id collisions when multiple charts are placed.
Pin Plotly, Kaleido, browser, and fonts for reproducible builds.

Exports are static: hover, zoom, callbacks, and animation frames are not
retained. SVG-native traces keep paths and text editable. Plotly WebGL traces
(such as `scattergl` and 3D surfaces) can embed raster images in SVG; use SVG
trace types when vector editability matters. Fonts must also be available to
CairoSVG for PDF/PNG export.
