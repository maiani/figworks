# Development

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validation

```bash
ruff format --check .
ruff check .
ty check
pytest
```

## Releases

The README is also the PyPI project page, where relative links do not resolve,
so its links and image are absolute and pinned to a release tag. When bumping
the version, point them at the new tag, regenerate the README figure with
`python docs/readme_figure.py`, and refresh `uv.lock`, which records the
project's own version: `uv lock`.

## Document layout

The FigWorks source is split into focused modules under `src/figworks/`:

| Module | Responsibility |
|--------|----------------|
| `core/document.py` | The canonical `lxml` SVG document, import, placeholders, fill. |
| `core/selectors.py` | Minimal `#id`, `.class`, and tag selection. |
| `core/units.py` | Physical unit parsing. |
| `figure/figure.py` | The public `Figure` API. |
| `figure/panel.py` | `Panel` regions and anchors. |
| `figure/anchors.py` | `Anchor` points. |
| `figure/layout.py` | `layout_svgs` grid assembly. |
| `matplotlib.py` | Matplotlib ⇄ SVG bridge (export, import, insert). |
| `_export.py` | Internal PDF and PNG export helpers. |
| `elements/` | Native shape, text, and arrow factories. |

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
