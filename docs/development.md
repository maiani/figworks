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

Pushing a `v*` tag runs `.github/workflows/publish.yml`: it checks that the tag
matches `figworks.__version__`, runs the whole CI workflow (including the TeX
job) on the tagged commit, builds and `twine check`s the distributions, and
publishes them to PyPI by trusted publishing from the `pypi` environment.

1. Check that the last CI run on `main` is green.
2. Bump `__version__` in `src/figworks/__init__.py`, move the changelog's
   Unreleased section under the new version, repoint the README, and run
   `uv lock`.
3. Push `main`, then only the new tag: `git push origin v0.8.0`. Never
   `git push --tags`: any pushed `v*` tag publishes.

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
