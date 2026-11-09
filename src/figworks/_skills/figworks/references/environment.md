# Environment and rendering

Use this reference for unfamiliar environments or failed exports. `python`
means the research project's chosen interpreter, not necessarily the shell default.

## Check the environment

Inspect the dependency file and existing environment before installing anything:

```bash
python -c 'import sys, figworks; print(sys.executable); print(figworks.__version__); print(figworks.__file__)'
```

FigWorks 0.10 requires Python 3.12 or newer. A source checkout or installed wheel
works; the starter does not need the FigWorks repository on `PYTHONPATH`. This
skill is bundled with the Python package. Copy it to any harness's skill folder
with `python -m figworks.skill install DESTINATION`, where `DESTINATION` is the
complete target folder including `figworks`. Copies include this reference and
the starter. Use `--overwrite` to refresh bundled files after a package upgrade;
local edits to those files will be replaced. `python -m figworks.skill path`
prints the source directory for direct reading or an editable development link.

When setup is part of the task, install the project-selected version into its
chosen environment and follow its lockfile policy. VecTeX is required; VecView,
VecWire, and `figworks[plotly]` are optional. Check installed public signatures
when using another version instead of silently upgrading to match a snippet.

## Fonts and TeX

PDF/PNG rendering needs Cairo and the requested system fonts. Font validation
uses `fc-match` and `fc-query`. The default paper theme uses TeX Gyre Heros.
Typical Debian/Ubuntu packages are `libcairo2`, `fonts-texgyre`,
`fonts-dejavu-core`, and `fontconfig`; check the actual environment first.
A successful `fc-match` can still return a substitute: inspect its family or run
FigWorks preflight. Provide the intended font or make a consistent, explicit
style choice rather than bypassing validation.

Ordinary Matplotlib mathtext needs no TeX installation. VecTeX needs the selected
engine (normally `pdflatex`), `dvisvgm`, the preamble's packages, and a PDF reader
backend for dvisvgm (the suite uses `mutool`). The standalone class and TeX Gyre
packages are common requirements. Matplotlib's `math: latex` mode additionally
needs `latex` and its usetex font packages. Follow the selected setup in the
[style guide](https://github.com/maiani/figworks/blob/main/docs/usage/styles.md).
Report missing tools and affected outputs accurately.

## Headless rendering

Set `MPLBACKEND=Agg` for a headless Matplotlib build. If the usual cache is not
writable, set `MPLCONFIGDIR` to a writable project or temporary directory.
Do not encode a workstation's absolute paths in a shared generator.

Plotly static export needs Kaleido and Chrome. `BROWSER_PATH` can select a working
browser executable when automatic discovery picks an unusable launcher. Browser
installation is a separate download; follow the task's environment-setup scope.
See the [Plotly guide](https://github.com/maiani/figworks/blob/main/docs/usage/plotly.md).

To inspect a generated PDF with an available Poppler installation:

```bash
pdftoppm -singlefile -scale-to 1600 -png figures/figure.pdf figures/pdf-preview
```

Open the resulting PNG with the environment's image viewer. Rendering a preview
alone is not visual inspection. Other PDF renderers/viewers are equally suitable.

## Documentation

Prefer documentation in a matching local checkout. Upstream links track
development; check their APIs against the installed version.

- [Figure and panels](https://github.com/maiani/figworks/blob/main/docs/usage/figure.md)
- [Grid layout](https://github.com/maiani/figworks/blob/main/docs/usage/layout.md)
- [Export and math](https://github.com/maiani/figworks/blob/main/docs/usage/export.md)
- [Preflight coverage](https://github.com/maiani/figworks/blob/main/docs/usage/preflight.md)
- [Gallery](https://github.com/maiani/figworks/blob/main/docs/gallery/index.md)

Gallery scripts offer composition patterns. Their illustrative models and page
sizes do not establish a new project's assumptions or submission requirements.
