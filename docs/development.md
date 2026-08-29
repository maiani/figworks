# Development

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validation

```bash
pytest
ruff check .
```

## Document layout

The FigForge source is split into focused modules under `src/figforge/`:

| Module | Responsibility |
|--------|----------------|
| `core/document.py` | The canonical `lxml` SVG document, import, placeholders, fill. |
| `core/selectors.py` | Minimal `#id`, `.class`, and tag selection. |
| `core/units.py` | Physical unit parsing. |
| `figure/figure.py` | The public `Figure` API. |
| `figure/panel.py` | `Panel` regions and anchors. |
| `figure/anchors.py` | `Anchor` points. |
| `figure/layout.py` | `layout_svgs` grid assembly. |
| `backends/matplotlib.py` | Matplotlib ⇄ SVG bridge (export, import, insert). |
| `backends/cairosvg.py` | PDF and PNG export. |
| `elements/` | Native shape, text, and arrow factories. |
| `themes/` | Small built-in `Theme` presets. |

## Documentation

This site is built with [Zensical](https://zensical.org). To preview it:

```bash
python -m pip install zensical
zensical serve
```

Then open <http://localhost:8000>. To produce a static build:

```bash
zensical build
```
