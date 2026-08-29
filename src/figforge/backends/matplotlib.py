"""Matplotlib SVG bridge."""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
from typing import Any, Mapping

import matplotlib.pyplot as plt
from lxml import etree
from matplotlib import rcParams
from matplotlib.offsetbox import DrawingArea, OffsetImage

from figforge.core.element import (
    copy_element,
    ensure_defs,
    fit_transform,
    local_name,
    parse_svg,
    register_ns,
    svg_intrinsic_size,
    svg_tag,
)
from figforge.core.document import element_box


@contextmanager
def mpl_svg_context():
    """Preserve text as SVG text while exporting Matplotlib figures."""

    old_fonttype = rcParams.get("svg.fonttype")
    rcParams["svg.fonttype"] = "none"
    try:
        yield
    finally:
        rcParams["svg.fonttype"] = old_fonttype


def mpl_to_svg(fig, *, id: str | None = None, transparent: bool = True, bbox_inches="tight") -> str:
    """Export a Matplotlib figure to an SVG string."""

    import io

    buffer = io.StringIO()
    with mpl_svg_context():
        fig.savefig(
            buffer,
            format="svg",
            transparent=transparent,
            bbox_inches=bbox_inches,
        )
    svg = buffer.getvalue()
    if id:
        root = parse_svg(svg)
        root.set("id", id)
        svg = etree.tostring(root, encoding="unicode")
    return svg


def set_gid(artist, gid: str):
    """Assign a semantic SVG ID to a Matplotlib artist."""

    artist.set_gid(gid)
    return artist


def connect(
    ax,
    gid: str,
    x: float = 0,
    y: float = 0,
    width: float = 1,
    height: float = 1,
):
    """Add a placeholder rectangle to a Matplotlib axes.

    The rectangle is exported with the given ``gid`` and can be replaced later
    with vector SVG content via :func:`insert`.
    """
    from matplotlib.patches import Rectangle

    patch = Rectangle((x, y), width, height)
    ax.add_artist(patch)
    patch.set_gid(gid)
    return patch


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
    from matplotlib.patches import Rectangle

    area = DrawingArea(width, height)
    patch = Rectangle((0, 0), width, height)
    area.add_artist(patch)
    patch.set_gid(gid)
    return area


def insert(
    replacements: Mapping[str, Any],
    fig=None,
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
    from figforge.core.element import resolve_svg_source

    if svg is None:
        svg = mpl_to_svg(fig) if fig is not None else _current_figure_svg()

    resolved = {key: resolve_svg_source(value) for key, value in replacements.items()}

    root = parse_svg(svg)
    idmap = {node.get("id"): node for node in root.iter() if node.get("id")}
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
        plt.savefig(buffer, format="svg")
    return buffer.getvalue()


def _swap_node(
    root: etree._Element,
    node: etree._Element,
    parent_map: Mapping[etree._Element, etree._Element],
    replacement_svg: str,
    preserve_aspect_ratio: bool,
) -> None:
    box = element_box(node)
    x, y, width, height = box
    parent = parent_map.get(node)
    index = list(parent).index(node) if parent is not None else 0
    if parent is not None:
        parent.remove(node)

    try:
        replacement_root = parse_svg(replacement_svg)
    except etree.XMLSyntaxError:
        raise ValueError("Replacement is not valid SVG")

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
