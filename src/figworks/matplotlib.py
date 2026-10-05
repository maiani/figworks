"""Matplotlib SVG bridge."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import matplotlib.pyplot as plt
from lxml import etree
from matplotlib import rc_context
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.offsetbox import DrawingArea, OffsetImage
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

from figworks.core.document import element_box
from figworks.core.element import (
    copy_element,
    ensure_defs,
    fit_transform,
    local_name,
    parse_svg,
    register_ns,
    svg_intrinsic_size,
    svg_tag,
)

if TYPE_CHECKING:
    from matplotlib import RcParams

    from figworks.style import Theme

# Matplotlib salts clip-path and marker ids with a random value unless one is set,
# and stamps the export date, so without these two settings no export is byte-identical.
SVG_METADATA = {"Date": None}


@contextmanager
def mpl_svg_context() -> Iterator[None]:
    """Keep text as SVG text and ids deterministic while exporting Matplotlib figures."""

    with rc_context({"svg.fonttype": "none", "svg.hashsalt": "figworks"}):
        yield


def theme_rc(theme: str | Path | Theme = "paper") -> RcParams:
    """The Matplotlib settings a style generates: its typeface, sizes, weights, colours.

    ``theme`` is a built-in name, a path to a ``style.md``, or a loaded
    :class:`~figworks.style.Theme`; see :meth:`Theme.rc` for the layers.
    Matplotlib fixes a text's font when the text is created but chooses math
    fonts when the figure is drawn, which for FigWorks is when it is placed, so
    apply the settings once at the top of the script::

        plt.rcParams.update(theme_rc("style.md"))
        mpl_fig, ax = plt.subplots(figsize=(3, 2))
        ax.set_xlabel(r"$\\omega / \\omega_0$")
    """
    from figworks.style import load_theme

    return load_theme(theme).rc()


def mpl_to_svg(
    fig: Figure,
    *,
    id: str | None = None,
    transparent: bool = True,
    bbox_inches: Literal["tight"] | Bbox | None = "tight",
) -> str:
    """Export a Matplotlib figure to an SVG string."""

    import io

    buffer = io.StringIO()
    with mpl_svg_context():
        fig.savefig(
            buffer,
            format="svg",
            transparent=transparent,
            bbox_inches=bbox_inches,
            metadata=SVG_METADATA,
        )
    svg = buffer.getvalue()
    if id:
        root = parse_svg(svg)
        root.set("id", id)
        svg = etree.tostring(root, encoding="unicode")
    return svg


# Matplotlib stamps creation dates into PDF and SVG; dropping them is what lets
# a regenerated file come out byte-identical.
_SAVE_METADATA = {"svg": SVG_METADATA, "pdf": {"CreationDate": None}}


def save_figure(fig: Figure, path: str | Path, *, dpi: float = 300) -> None:
    """Write a Matplotlib figure deterministically, after checking its fonts.

    The same file comes out on every run: SVG ids are pinned and creation dates
    dropped, as for figures placed in FigWorks.  Fonts are checked first, as
    :meth:`figworks.Figure.save` does, so a missing face raises
    :class:`~figworks.fonts.FontError` instead of being substituted.
    """
    from figworks.fonts import check_fonts

    output = Path(path)
    suffix = output.suffix.lower().lstrip(".")
    if suffix not in ("svg", "pdf", "png"):
        raise ValueError(f"Unsupported export format: {output.suffix}")
    check_fonts(mpl_to_svg(fig))
    with mpl_svg_context():
        fig.savefig(output, dpi=dpi, metadata=_SAVE_METADATA.get(suffix))


def axes_frame(fig: Figure) -> tuple[float, float, float, float]:
    """The union of a figure's visible axes, as ``(width, height, x, y)`` in points.

    Measured from the figure's top-left corner, y downward, which is the
    coordinate system of the figure's own SVG export with ``bbox_inches=None``.
    The order matches :func:`~figworks.core.element.svg_intrinsic_size`, so the
    frame can stand in for a document's intrinsic box when fitting.  Read it
    after the figure is drawn, so a layout engine's positions are final.
    """
    frames = [ax.get_position() for ax in fig.axes if ax.get_visible()]
    if not frames:
        raise ValueError("the figure has no visible axes to align by")
    width_pt, height_pt = (float(v) * 72 for v in fig.get_size_inches())
    left = min(frame.x0 for frame in frames) * width_pt
    right = max(frame.x1 for frame in frames) * width_pt
    top = (1 - max(frame.y1 for frame in frames)) * height_pt
    bottom = (1 - min(frame.y0 for frame in frames)) * height_pt
    return right - left, bottom - top, left, top


def set_gid[ArtistT: Artist](artist: ArtistT, gid: str) -> ArtistT:
    """Assign a semantic SVG ID to a Matplotlib artist."""

    artist.set_gid(gid)
    return artist


def connect(
    ax: Axes,
    gid: str,
    x: float = 0,
    y: float = 0,
    width: float = 1,
    height: float = 1,
) -> Rectangle:
    """Add a placeholder rectangle to a Matplotlib axes.

    The rectangle is exported with the given ``gid`` and can be replaced later
    with vector SVG content via :func:`insert`.
    """

    patch = Rectangle((x, y), width, height)
    ax.add_artist(patch)
    patch.set_gid(gid)
    return patch


def compose(
    replacements: Mapping[Any, Any],
    fig: Figure | None = None,
    *,
    preserve_aspect_ratio: bool = True,
) -> str:
    """Place SVG-producing sources into Matplotlib axes and return SVG.

    ``replacements`` maps each target axes to an SVG string/path, Matplotlib
    figure, VecTeX fragment, or another SVG document provider.  This is the
    lightweight entry point for callers that do not need :class:`Figure`.
    """

    target_figure = fig if fig is not None else plt.gcf()
    by_id: dict[str, Any] = {}
    placeholders: list[Rectangle] = []
    for index, (axes, source) in enumerate(replacements.items()):
        if not hasattr(axes, "add_artist") or not hasattr(axes, "transAxes"):
            raise TypeError("compose replacement keys must be Matplotlib axes")
        if getattr(axes, "figure", target_figure) is not target_figure:
            raise ValueError("all replacement axes must belong to fig")
        gid = f"figworks-compose-{index}"
        placeholder = Rectangle((0, 0), 1, 1, transform=axes.transAxes)
        placeholder.set_gid(gid)
        axes.add_artist(placeholder)
        placeholders.append(placeholder)
        by_id[gid] = source
    try:
        return insert(
            by_id,
            fig=target_figure,
            preserve_aspect_ratio=preserve_aspect_ratio,
        )
    finally:
        for placeholder in placeholders:
            placeholder.remove()


def svg_to_image_artist(
    svg_string: str,
    gid: str | None = None,
    *,
    zoom: float = 1.0,
) -> OffsetImage:
    """Import an SVG string as a Matplotlib offset image artist.

    The returned artist can be placed in a figure/axes with ``ax.add_artist`` or
    an ``OffsetBox``. It is embedded as a raster for preview. When the figure is
    exported to SVG, replace the raster with the original vector SVG via
    :func:`insert`, keyed by ``gid``.
    """
    import cairosvg

    png = cairosvg.svg2png(bytestring=svg_string.encode("utf-8"))
    image = plt.imread(BytesIO(png), format="png")
    offset = OffsetImage(image, zoom=zoom)
    if gid is not None:
        properties = offset.properties()
        if properties.get("children"):
            properties["children"][0].set_gid(gid)
    return offset


def box_artist(width: float, height: float, gid: str) -> DrawingArea:
    """Return a replaceable Matplotlib drawing area."""

    area = DrawingArea(width, height)
    patch = Rectangle((0, 0), width, height)
    area.add_artist(patch)
    patch.set_gid(gid)
    return area


def insert(
    replacements: Mapping[str, Any],
    fig: Figure | None = None,
    svg: str | None = None,
    *,
    preserve_aspect_ratio: bool = True,
) -> str:
    """Replace SVG elements by id with vector SVG content.

    ``replacements`` maps an ``id``/gid present in the SVG to a Matplotlib
    figure, an SVG file path, or an SVG string. When ``fig`` is provided it is
    used to produce the base SVG; otherwise ``svg`` is edited in place. The
    returned SVG string has each matching element replaced with the imported
    vector content, scaled and positioned to fit the original element's box.
    """
    from figworks.core.element import resolve_svg_source

    if svg is None:
        svg = mpl_to_svg(fig) if fig is not None else _current_figure_svg()

    resolved = {key: resolve_svg_source(value) for key, value in replacements.items()}

    root = parse_svg(svg)
    idmap = {node_id: node for node in root.iter() if (node_id := node.get("id"))}
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for key, replacement in resolved.items():
        node = idmap.get(key)
        if node is None:
            raise UserWarning(f"Could not find id {key!r} in SVG. Found: {sorted(idmap)}")
        _swap_node(root, node, parent_map, replacement, preserve_aspect_ratio)

    register_ns(root)
    return etree.tostring(root, encoding="unicode", method="xml")


def _current_figure_svg() -> str:
    import io

    buffer = io.StringIO()
    with mpl_svg_context():
        plt.savefig(buffer, format="svg", metadata=SVG_METADATA)
    return buffer.getvalue()


def _swap_node(
    root: etree._Element,
    node: etree._Element,
    parent_map: Mapping[etree._Element, etree._Element],
    replacement_svg: str,
    preserve_aspect_ratio: bool,
) -> None:
    box = element_box(node)
    parent = parent_map.get(node)
    index = list(parent).index(node) if parent is not None else 0
    if parent is not None:
        parent.remove(node)

    try:
        replacement_root = parse_svg(replacement_svg)
    except etree.XMLSyntaxError as err:
        raise ValueError("Replacement is not valid SVG") from err

    transform = fit_transform(
        box, svg_intrinsic_size(replacement_svg), preserve_aspect_ratio=preserve_aspect_ratio
    )

    container = parent if parent is not None else root
    group = etree.Element(svg_tag("g"), {"transform": transform})
    container.insert(index, group)

    for child in replacement_root:
        copied = copy_element(child)
        if local_name(child) == "defs":
            ensure_defs(root).extend(list(copied))
        else:
            group.append(copied)
            if not preserve_aspect_ratio:
                copied.set("preserveAspectRatio", "none")
