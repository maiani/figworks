"""A publication's visual vocabulary, written as one ``style.md`` document.

The YAML frontmatter holds the design tokens; the Markdown body is the style
guide for the humans and agents making figures -- what each colour means, which
weight to use for what.  Code reads only the frontmatter::

    ---
    base: aps                      # a built-in style, or another style.md
    matplotlib: ./cosmetics.mplstyle  # optional Matplotlib styles underneath
    page:
      column: 86mm                 # named lengths: Figure(width=theme.page["column"], ...)
    font:
      size: 7pt
    color:
      spin_up: "#d62828"
      spin_down: "#1f6fd1"
    cycle: [spin_up, spin_down]
    rcparams:                      # raw Matplotlib settings, applied last
      legend.frameon: false
    ---

    # Style guide
    Red is always s = +1 ...

A style states only what differs from its ``base``.  The built-ins -- ``paper``,
``presentation``, and the journal styles ``nature``, ``aps``, and ``ieee`` -- are
themselves ``style.md`` files shipped with FigWorks.
Matplotlib settings are generated in four layers: Matplotlib's defaults, the
``matplotlib`` styles of the chain, the settings the tokens imply, and
``rcparams`` overrides.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from figworks.core.units import to_px

if TYPE_CHECKING:
    from matplotlib import RcParams

STYLES_DIR = Path(__file__).resolve().parent / "styles"
BUILT_IN = ("paper", "presentation", "nature", "aps", "ieee")

_TOP_LEVEL = {"base", "matplotlib", "page", "font", "line", "color", "cycle", "marker", "rcparams"}


@dataclass(frozen=True)
class Font:
    """The typeface and its size scale, sizes in pt."""

    family: str
    size: float
    label: float
    tick: float
    title: float
    legend: float
    panel_label: float


@dataclass(frozen=True)
class Lines:
    """Line weights in pt: data curves, axes frames and ticks, and grids."""

    data: float
    frame: float
    hairline: float


@dataclass(frozen=True)
class Theme:
    """A loaded style: its tokens, its Matplotlib layers, and where it came from.

    Load one with :func:`load_theme`, from a built-in name or a ``style.md``.
    """

    name: str
    font: Font
    line: Lines
    color: Mapping[str, str]
    page: Mapping[str, str]
    cycle: tuple[str, ...]
    marker: float
    matplotlib: tuple[str, ...]
    rcparams: Mapping[str, Any]

    # --- values FigWorks' own elements use -------------------------------
    @property
    def font_family(self) -> str:
        return self.font.family

    @property
    def base_font_size(self) -> str:
        return f"{self.font.size:g}pt"

    @property
    def panel_label_font_size(self) -> str:
        return f"{self.font.panel_label:g}pt"

    @property
    def stroke(self) -> str:
        return self.color["ink"]

    @property
    def stroke_width(self) -> str:
        return f"{self.line.data:g}pt"

    # --- values for any producer, as plain numbers -----------------------
    def px(self, token: str) -> float:
        """A length token in px, for producers that draw in px: ``theme.px("line.frame")``."""
        group, _, key = token.partition(".")
        source: Any = {"font": self.font, "line": self.line}.get(group)
        if group == "marker" and not key:
            return self.marker * 96 / 72
        if source is None or key not in {f.name for f in fields(source)} or key == "family":
            raise KeyError(f"no length token {token!r}")
        return float(getattr(source, key)) * 96 / 72

    def rc(self) -> RcParams:
        """The Matplotlib settings this style generates, without touching Matplotlib's state.

        Layered over Matplotlib's defaults: apply with ``plt.style.use("default")``
        followed by ``plt.rcParams.update(theme.rc())``, as
        :class:`~figworks.FigureCollection` does.
        """
        import matplotlib as mpl
        from cycler import cycler
        from matplotlib import style as mpl_style

        settings: dict[str, Any] = {}
        for entry in self.matplotlib:
            path = Path(entry)
            if path.suffix == ".mplstyle":
                layer = mpl.rc_params_from_file(path, use_default_template=False)
            elif entry in mpl_style.library:
                layer = mpl_style.library[entry]
            else:
                raise ValueError(f"style {self.name}: no Matplotlib style {entry!r}")
            for key, value in layer.items():
                settings[str(key)] = value
        family, ink = self.font.family, self.color["ink"]
        settings.update(
            {
                "font.family": [family],
                "font.size": self.font.size,
                "mathtext.fontset": "custom",
                "mathtext.rm": family,
                "mathtext.it": f"{family}:italic",
                "mathtext.bf": f"{family}:bold",
                "mathtext.sf": family,
                "axes.labelsize": self.font.label,
                "axes.titlesize": self.font.title,
                "xtick.labelsize": self.font.tick,
                "ytick.labelsize": self.font.tick,
                "legend.fontsize": self.font.legend,
                "legend.title_fontsize": self.font.legend,
                "lines.linewidth": self.line.data,
                "lines.markersize": self.marker,
                "axes.linewidth": self.line.frame,
                "patch.linewidth": self.line.frame,
                "xtick.major.width": self.line.frame,
                "ytick.major.width": self.line.frame,
                "xtick.minor.width": self.line.hairline,
                "ytick.minor.width": self.line.hairline,
                "grid.linewidth": self.line.hairline,
                "text.color": ink,
                "axes.labelcolor": ink,
                "axes.edgecolor": ink,
                "xtick.color": ink,
                "ytick.color": ink,
            }
        )
        if self.cycle:
            settings["axes.prop_cycle"] = cycler(color=list(self.cycle))
        settings.update(self.rcparams)
        try:
            return mpl.RcParams(settings)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"style {self.name}: {exc}") from exc


def read_frontmatter(path: Path) -> dict[str, Any]:
    """The YAML frontmatter of a Markdown file, as a mapping (empty if none)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: a style.md starts with a '---' YAML frontmatter block")
    _, _, rest = text.partition("\n")
    end = rest.find("\n---")
    if end < 0:
        raise ValueError(f"{path}: the frontmatter is not closed by a '---' line")
    data = yaml.safe_load(rest[:end]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: the frontmatter must be a mapping")
    unknown = sorted(set(data) - _TOP_LEVEL)
    if unknown:
        raise ValueError(
            f"{path}: unknown key(s) {', '.join(unknown)}; expected {sorted(_TOP_LEVEL)}"
        )
    return data


def _style_path(source: str | Path, relative_to: Path | None) -> Path:
    if isinstance(source, str) and source in BUILT_IN:
        return STYLES_DIR / f"{source}.md"
    path = Path(source)
    if relative_to is not None and not path.is_absolute():
        path = relative_to / path
    if not path.is_file():
        raise FileNotFoundError(
            f"no style {source!r}: not a built-in ({', '.join(BUILT_IN)}) or a file"
        )
    return path.resolve()


def _merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Nested mappings merge key by key; anything else is replaced."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _resolve(path: Path, seen: tuple[Path, ...]) -> dict[str, Any]:
    """A style's frontmatter merged over its whole base chain."""
    if path in seen:
        chain = " -> ".join(p.name for p in (*seen, path))
        raise ValueError(f"style bases form a cycle: {chain}")
    data = read_frontmatter(path)
    layers = data.pop("matplotlib", None) or []
    if isinstance(layers, str):
        layers = [layers]
    # Paths are relative to the file that names them; style names pass through.
    data["matplotlib"] = [
        str((path.parent / entry).resolve()) if str(entry).endswith(".mplstyle") else str(entry)
        for entry in layers
    ]
    base = data.pop("base", None if path == STYLES_DIR / "paper.md" else "paper")
    if base is None:
        return data
    parent = _resolve(_style_path(base, path.parent), (*seen, path))
    data["matplotlib"] = parent.get("matplotlib", []) + data["matplotlib"]
    return _merge(parent, data)


def _pt(value: Any, token: str) -> float:
    try:
        # Rounded so a length given in pt comes back exactly, not as 6.999999999999999.
        text = str(value) if not isinstance(value, (int, float)) else f"{value}pt"
        return round(to_px(text) * 72 / 96, 9)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"{token}: expected a length such as '0.5pt' or '0.2mm', got {value!r}"
        ) from exc


def _section[T: (Font, Lines)](cls: type[T], data: Mapping[str, Any], name: str) -> T:
    values = dict(data.get(name) or {})
    names = [f.name for f in fields(cls)]
    unknown = sorted(set(values) - set(names))
    if unknown:
        raise ValueError(f"unknown {name} token(s) {', '.join(unknown)}; expected {names}")
    missing = sorted(set(names) - set(values))
    if missing:
        raise ValueError(f"{name} token(s) {', '.join(missing)} are not set anywhere in the chain")
    tokens: dict[str, Any] = {
        key: str(value) if key == "family" else _pt(value, f"{name}.{key}")
        for key, value in values.items()
    }
    return cls(**tokens)


def load_theme(source: str | Path | Theme = "paper") -> Theme:
    """Load a style: a :class:`Theme`, a built-in name, or a path to a ``style.md``."""
    if isinstance(source, Theme):
        return source
    path = _style_path(source, None)
    data = _resolve(path, ())
    colors = {str(key): str(value) for key, value in (data.get("color") or {}).items()}
    page = {str(key): str(value) for key, value in (data.get("page") or {}).items()}
    for key, value in page.items():
        _pt(value, f"page.{key}")  # validated here; kept as written, ready for Figure(width=...)
    if "ink" not in colors:
        raise ValueError("color.ink is not set anywhere in the chain")
    cycle = tuple(colors.get(str(entry), str(entry)) for entry in data.get("cycle") or ())
    return Theme(
        name=path.stem if path.parent == STYLES_DIR else str(path),
        font=_section(Font, data, "font"),
        line=_section(Lines, data, "line"),
        color=colors,
        page=page,
        cycle=cycle,
        marker=_pt(data.get("marker", "3pt"), "marker"),
        matplotlib=tuple(data.get("matplotlib") or ()),
        rcparams=dict(data.get("rcparams") or {}),
    )


__all__ = ["BUILT_IN", "Font", "Lines", "Theme", "load_theme", "read_frontmatter"]
