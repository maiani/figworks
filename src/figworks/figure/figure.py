"""Public figure assembly API."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from figworks._export import svg_to_pdf, svg_to_png
from figworks.core.document import SVGDocument
from figworks.core.selectors import Selection
from figworks.core.units import to_px
from figworks.elements.arrows import ensure_arrow_marker, line_arrow
from figworks.elements.shapes import circle, ellipse, line, path, polyline, rect
from figworks.elements.text import text_element
from figworks.figure.anchors import Anchor
from figworks.figure.grid import Gap, GridLayout, Margins, grid_boxes
from figworks.figure.panel import Panel
from figworks.fonts import check_fonts
from figworks.style import Theme, load_theme

if TYPE_CHECKING:
    from lxml import etree


class Figure:
    """Top-level FigWorks SVG figure."""

    def __init__(
        self,
        width: str | int | float,
        height: str | int | float,
        theme: str | Path | Theme = "paper",
    ) -> None:
        """A canvas of the given physical size, styled by ``theme``.

        ``theme`` is a built-in style name (``"paper"``, ``"presentation"``,
        ``"nature"``, ``"aps"``, ``"ieee"``), a path to a ``style.md``, or a
        loaded :class:`~figworks.style.Theme`.
        """
        self.width = width
        self.height = height
        self.theme = load_theme(theme)
        self.document = SVGDocument(width, height)
        # Inherited by every source that names no font of its own.
        self.document.root.set("font-family", self.theme.font_family)
        self.panels: dict[str, Panel] = {}

    def panel(
        self,
        id: str,
        x: str | int | float,
        y: str | int | float,
        w: str | int | float,
        h: str | int | float,
    ) -> Panel:
        if id in self.panels:
            raise ValueError(f"Panel already exists: {id!r}")
        panel = Panel(self, id, to_px(x), to_px(y), to_px(w), to_px(h))
        self.panels[id] = panel
        return panel

    def grid(
        self,
        layout: GridLayout,
        *,
        width_ratios: Sequence[float] | None = None,
        height_ratios: Sequence[float] | None = None,
        margins: Margins = 0,
        gap: Gap = 0,
    ) -> dict[str, Panel]:
        """Create named panels from a rectangular grid, in first-occurrence order.

        Repeat an ID across cells to span a filled rectangle; ``None`` leaves
        a cell empty. Ratios divide the space remaining after physical margins
        and gaps. A spanning panel includes the gaps between its cells::

            panels = fig.grid(
                [["device", "device"], ["spectrum", "response"]],
                width_ratios=(2, 1), height_ratios=(1, 2),
                margins="8mm", gap=("12mm", "16mm"),
            )
            panels["device"].add(scene, id="device-scene")

        ``margins`` is one length or ``(top, right, bottom, left)``; ``gap``
        is one length or ``(row_gap, column_gap)``. Bare numbers are px.
        Leave room for labels around panels used with ``fit="axes"``.
        All inputs and existing panel IDs are checked before creating panels.
        Panels are fixed rectangles; resizing requires a new figure and grid.
        """
        boxes = grid_boxes(
            layout,
            self.document.width_px,
            self.document.height_px,
            width_ratios=width_ratios,
            height_ratios=height_ratios,
            margins=margins,
            gap=gap,
        )
        duplicates = boxes.keys() & self.panels.keys()
        if duplicates:
            raise ValueError(f"Panel already exists: {sorted(duplicates)[0]!r}")
        return {name: self.panel(name, *box) for name, box in boxes.items()}

    def select(self, selector: str) -> Selection:
        return self.document.select(selector)

    def text(
        self,
        text: str,
        x: str | int | float,
        y: str | int | float,
        id: str | None = None,
        class_: str | None = None,
        **attrs: Any,
    ) -> etree._Element:
        attrs.setdefault("font_family", self.theme.font_family)
        attrs.setdefault("font_size", self.theme.base_font_size)
        node = text_element(text, x=to_px(x), y=to_px(y), id=id, class_=class_, **attrs)
        return self.document.append(node)

    def label(
        self,
        text: str,
        anchor: Anchor | tuple[str | int | float, str | int | float],
        id: str | None = None,
        dx: str | int | float = "-3mm",
        dy: str | int | float = "-2mm",
        **attrs: Any,
    ) -> etree._Element:
        x, y = self._point(anchor)
        attrs.setdefault("font_family", self.theme.font_family)
        attrs.setdefault("font_size", self.theme.panel_label_font_size)
        attrs.setdefault("font_weight", "bold")
        return self.text(
            text,
            x + to_px(dx),
            y + to_px(dy),
            id=id,
            class_="figworks-label",
            **attrs,
        )

    def arrow(
        self,
        id: str,
        start: Anchor | tuple[str | int | float, str | int | float],
        end: Anchor | tuple[str | int | float, str | int | float],
        class_: str | None = None,
        **attrs: Any,
    ) -> etree._Element:
        ensure_arrow_marker(self.document, stroke=attrs.get("stroke", self.theme.stroke))
        x1, y1 = self._point(start)
        x2, y2 = self._point(end)
        attrs.setdefault("stroke", self.theme.stroke)
        attrs.setdefault("stroke_width", self.theme.stroke_width)
        return self.document.append(line_arrow(x1, y1, x2, y2, id=id, class_=class_, **attrs))

    def line(self, **attrs: Any) -> etree._Element:
        return self.document.append(line(**attrs))

    def rect(self, **attrs: Any) -> etree._Element:
        return self.document.append(rect(**attrs))

    def circle(self, **attrs: Any) -> etree._Element:
        return self.document.append(circle(**attrs))

    def ellipse(self, **attrs: Any) -> etree._Element:
        return self.document.append(ellipse(**attrs))

    def polyline(self, **attrs: Any) -> etree._Element:
        return self.document.append(polyline(**attrs))

    def path(self, **attrs: Any) -> etree._Element:
        return self.document.append(path(**attrs))

    def placeholder(
        self,
        id: str,
        x: str | int | float,
        y: str | int | float,
        w: str | int | float,
        h: str | int | float,
        label: str | None = None,
    ) -> etree._Element:
        x_px, y_px, w_px, h_px = to_px(x), to_px(y), to_px(w), to_px(h)
        return self.document.placeholder(id, x_px, y_px, w_px, h_px, label=label)

    def fill(
        self,
        id: str,
        source: Any,
        *,
        preserve_aspect_ratio: bool = True,
    ) -> etree._Element:
        """Replace a placeholder (or any element by id) with imported content.

        Accepts a matplotlib figure, an SVG file path, or an SVG string.
        """
        from figworks.core.element import resolve_svg_source

        return self.document.fill(
            id,
            resolve_svg_source(source),
            preserve_aspect_ratio=preserve_aspect_ratio,
        )

    def fill_plane(self, id: str, source: Any) -> etree._Element:
        """Fill a unit-square group by id with content normalized to fit it.

        Use this to place a plot, equation, or image *in* a plane of an
        ``vecview`` scene, rather than flat on top of the figure::

            scene.plane(15, origin, u_edge, v_edge, id="plot-plane")
            panel.add(scene, id="geometry")
            fig.fill_plane("plot-plane", mpl_fig)

        Accepts a Matplotlib figure, an SVG file path, an SVG string, or any
        object exposing ``to_svg_document()``.

        The content is normalized onto the unit square, so shape the target
        rectangle to the content's aspect ratio to avoid stretching it.
        """
        from figworks.core.element import resolve_svg_source

        return self.document.fill_plane(id, resolve_svg_source(source))

    def fill_slot(self, id: str, source: Any) -> etree._Element:
        """Fill an anchor group by id with content kept at its own size.

        Use this to pin an upright label or inset to a point of a VecView
        scene.  The scene reserves the slot; the label keeps its declared
        physical size however the scene is scaled to fit its panel::

            scene.slot(45, tip, w, h, align="west", dx=1.6, id="label-x")
            panel.add(scene, id="geometry")
            fig.fill_slot("label-x", vectex.render("$x$", size_pt=8))

        Accepts a Matplotlib figure, an SVG file path, an SVG string, or any
        object exposing ``to_svg_document()``.

        The room the scene reserved for the slot matches the content exactly
        only when the scene is placed at 1:1; scaled down, the content
        overhangs its reservation by the same factor.
        """
        from figworks.core.element import resolve_svg_source

        return self.document.fill_slot(id, resolve_svg_source(source))

    def add(
        self,
        source: Any,
        *,
        x: str | int | float,
        y: str | int | float,
        w: str | int | float,
        h: str | int | float,
        id: str | None = None,
        preserve_aspect_ratio: bool = True,
        fit: Literal["content", "axes", "none"] = "content",
        align: str = "center",
    ) -> etree._Element:
        """Place any supported SVG-producing source in a figure box.

        ``fit="content"`` scales the source's drawn content to fit the box.  For
        a Matplotlib figure, ``fit="axes"`` fits its *axes frame* instead -- the
        union of its axes -- and lets tick and axis labels hang outside the
        box.  Panels placed that way have frames exactly where their boxes are,
        so frames in a row line up whatever their labels.  With a figure from
        :meth:`Panel.subplots`, the frame is the box's size and the plot is
        placed at 1:1, so its text keeps its nominal size.

        ``fit="none"`` scales nothing: the source keeps the physical size its
        document declares, so an 8 pt label prints at 8 pt, and overhangs the
        box if it is larger.  ``align`` (``"center"``, ``"north"``,
        ``"northwest"``, …) puts that point of the content on the same point of
        the box; with the other fits it places content in the room a kept
        aspect ratio leaves over.
        """
        from figworks.core.element import fit_transform, natural_transform, resolve_svg_source

        if fit == "axes":
            from matplotlib.figure import Figure as MplFigure

            from figworks.matplotlib import axes_frame, mpl_to_svg

            if not isinstance(source, MplFigure):
                raise ValueError("fit='axes' needs a Matplotlib figure")
            # Export first: drawing applies any layout engine, fixing the frame.
            svg = mpl_to_svg(source, bbox_inches=None)
            transform = fit_transform(
                (to_px(x), to_px(y), to_px(w), to_px(h)),
                axes_frame(source),
                preserve_aspect_ratio=preserve_aspect_ratio,
                align=align,
            )
            return self.document.import_svg(svg, id=id, transform=transform)
        if fit == "none":
            svg = resolve_svg_source(source)
            box = (to_px(x), to_px(y), to_px(w), to_px(h))
            transform = natural_transform(box, svg, align=align)
            return self.document.import_svg(svg, id=id, transform=transform)
        if fit != "content":
            raise ValueError(f"fit must be 'content', 'axes', or 'none', got {fit!r}")
        return self.document.place(
            resolve_svg_source(source),
            to_px(x),
            to_px(y),
            to_px(w),
            to_px(h),
            id=id,
            preserve_aspect_ratio=preserve_aspect_ratio,
            align=align,
        )

    def save(self, path: str | Path, dpi: int = 300) -> None:
        """Write the figure as ``.svg``, ``.pdf``, or ``.png``.

        PDF and PNG are rendered on this machine, so before rendering every font
        the figure names is checked: a missing family or glyph raises
        :class:`~figworks.fonts.FontError` rather than silently rendering in a
        substitute.  SVG is written as is; its fonts are the viewer's concern.
        """
        output = Path(path)
        suffix = output.suffix.lower()
        svg = self.document.to_string()
        if suffix == ".svg":
            output.write_text(svg, encoding="utf-8")
            return
        if suffix in (".pdf", ".png"):
            check_fonts(svg)
        if suffix == ".pdf":
            svg_to_pdf(svg, output)
            return
        if suffix == ".png":
            svg_to_png(svg, output, dpi=dpi)
            return
        raise ValueError(f"Unsupported export format: {output.suffix}")

    def _point(
        self,
        point: Anchor | tuple[str | int | float, str | int | float],
    ) -> tuple[float, float]:
        if isinstance(point, Anchor):
            return point.as_tuple()
        x, y = point
        return to_px(x), to_px(y)
