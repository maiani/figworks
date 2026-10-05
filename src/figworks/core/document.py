"""Internal SVG document engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import svg
from lxml import etree

from figworks.core.element import (
    accumulated_scale,
    copy_element,
    ensure_defs,
    fit_transform,
    local_name,
    parse_svg,
    resolve_id_collisions,
    svg_intrinsic_size,
    svg_kwargs,
    svg_physical_size,
    svg_to_lxml,
)
from figworks.core.selectors import Selection, select
from figworks.core.units import px_decimal, svg_length, to_px

# Which point of slot content sits on the slot's anchor, as fractions of its size.
SLOT_ALIGN: dict[str, tuple[float, float]] = {
    "center": (0.5, 0.5),
    "north": (0.5, 0.0),
    "south": (0.5, 1.0),
    "east": (1.0, 0.5),
    "west": (0.0, 0.5),
    "northeast": (1.0, 0.0),
    "northwest": (0.0, 0.0),
    "southeast": (1.0, 1.0),
    "southwest": (0.0, 1.0),
}


class SVGDocument:
    """Canonical lxml-backed SVG document."""

    def __init__(self, width: str | int | float, height: str | int | float):
        self._imports = 0
        self.width = svg_length(width)
        self.height = svg_length(height)
        self.width_px = to_px(width)
        self.height_px = to_px(height)
        # The canvas is declared in physical units but every element is placed in
        # px user units, so the root needs a viewBox to bind the two.  Without it
        # a renderer maps one user unit to one px at its own default 96 DPI while
        # sizing the canvas from the physical attributes, and any export above
        # 96 DPI leaves the content in a corner at the wrong scale.
        self.root = svg_to_lxml(
            svg.SVG(
                viewBox=svg.ViewBoxSpec(0, 0, self.width_px, self.height_px),
                extra={"version": "1.1"},
            ),
            raw={"width": self.width, "height": self.height},
        )

    def element(self, tag: str, text: str | None = None, **attrs: Any) -> etree._Element:
        constructors = {
            "circle": svg.Circle,
            "ellipse": svg.Ellipse,
            "g": svg.G,
            "line": svg.Line,
            "path": svg.Path,
            "polyline": svg.Polyline,
            "rect": svg.Rect,
            "text": svg.Text,
        }
        try:
            constructor = constructors[tag]
        except KeyError as exc:
            raise ValueError(f"Unsupported native SVG element: {tag!r}") from exc
        return svg_to_lxml(constructor(text=text, **svg_kwargs(attrs)))

    def append(
        self,
        element: etree._Element,
        parent: etree._Element | None = None,
    ) -> etree._Element:
        # `parent or self.root` would silently retarget the root: an lxml
        # element with no children is falsy, so an empty group is discarded.
        (self.root if parent is None else parent).append(element)
        return element

    def group(
        self,
        id: str | None = None,
        class_: str | None = None,
        transform: str | None = None,
        parent: etree._Element | None = None,
    ) -> etree._Element:
        group = svg_to_lxml(
            svg.G(id=id, class_=None if class_ is None else [class_]),
            raw={"transform": transform},
        )
        return self.append(group, parent)

    def defs(self) -> etree._Element:
        return ensure_defs(self.root)

    def import_svg(
        self,
        svg_string: str,
        id: str | None = None,
        transform: str | None = None,
        parent: etree._Element | None = None,
        *,
        namespace: str | None = None,
    ) -> etree._Element:
        """Import an SVG document's content as a group, keeping its ids unique.

        Imported ids are kept unless one already exists in this document; a
        colliding id is prefixed with ``namespace`` (default: ``id``) and its
        references inside the content follow.  See
        :func:`~figworks.core.element.resolve_id_collisions`.
        """
        if id is not None and self.root.find(f".//*[@id='{id}']") is not None:
            raise ValueError(f"Id {id!r} is already used in this figure")
        imported_root = parse_svg(svg_string)
        group = self.group(id=id, transform=transform, parent=parent)
        self._imports += 1
        prefix = namespace or id or f"import{self._imports}"
        for duplicate in resolve_id_collisions(imported_root, self.root, prefix):
            # Identical to a definition already in the document: share that one.
            parent = duplicate.getparent()
            if parent is not None:
                parent.remove(duplicate)

        for child in imported_root:
            if local_name(child) == "defs":
                self.defs().extend(copy_element(definition) for definition in child)
            else:
                group.append(copy_element(child))

        return group

    def placeholder(
        self,
        id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str | None = None,
    ) -> etree._Element:
        """Create a rectangular placeholder that can be filled later by id.

        The placeholder is drawn with a dashed outline so it is visible while
        composing a figure.
        """
        rect = svg_to_lxml(
            svg.Rect(
                id=id,
                class_=["figworks-placeholder"],
                x=px_decimal(x),
                y=px_decimal(y),
                width=px_decimal(w),
                height=px_decimal(h),
                fill="none",
                stroke="#999999",
                stroke_width=px_decimal(0.5),
                stroke_dasharray=[4, 3],
            )
        )
        self.append(rect)
        if label is not None:
            self.append(
                svg_to_lxml(
                    svg.Text(
                        text=label,
                        x=px_decimal(x + w / 2),
                        y=px_decimal(y + h / 2),
                        class_=["figworks-placeholder-label"],
                        extra={"data-figworks-placeholder": id},
                        text_anchor="middle",
                        dominant_baseline="middle",
                    )
                )
            )
        return rect

    def fill(
        self,
        id: str,
        svg_string: str,
        *,
        preserve_aspect_ratio: bool = True,
    ) -> etree._Element:
        """Replace the placeholder (or any element) with imported SVG content.

        The content is positioned and scaled to fit inside the target element's
        bounding box, swapping vector SVG content in by id.

        Returns the wrapping group that holds the imported content.
        """
        targets = self.select(f"#{id}")
        if len(targets) == 0:
            raise KeyError(f"No element with id {id!r} in document")
        target = targets.nodes[0]
        box = element_box(target)
        for label in self.root.iter():
            if label.get("data-figworks-placeholder") == id:
                parent = label.getparent()
                if parent is not None:
                    parent.remove(label)
        return self._place_in_placeholder(target, box, svg_string, preserve_aspect_ratio)

    def fill_plane(self, id: str, svg_string: str) -> etree._Element:
        """Fill a unit-square group with SVG content, normalized to fit it.

        The target is a group whose own transform maps content coordinates in
        ``[0, 1]^2`` onto wherever it belongs -- typically an ``vecview`` scene
        plane, whose transform sends the unit square onto a rectangle of a world
        plane, so the content ends up lying *in* the scene rather than on top of
        it.  This method only normalizes: it leaves the target's transform alone
        and appends the content beneath it.

        The normalization is non-uniform by construction -- content of any size
        is mapped onto the same unit square -- so the target rectangle must be
        shaped to the content's aspect ratio or the content comes out stretched.
        For an ``vecview`` plane that means ``|u_edge| / |v_edge|`` equal to the
        content's ``width / height``.

        Returns the wrapping group holding the imported content.
        """
        targets = self.select(f"#{id}")
        if len(targets) == 0:
            raise KeyError(f"No element with id {id!r} in document")
        target = targets.nodes[0]

        width, height, min_x, min_y = svg_intrinsic_size(svg_string)
        if not width or not height:
            raise ValueError(f"Content for {id!r} has no intrinsic size to normalize")

        shift = f" translate({-min_x:g} {-min_y:g})" if (min_x or min_y) else ""
        transform = f"scale({1 / width:g} {1 / height:g}){shift}"
        return self.import_svg(svg_string, transform=transform, parent=target, namespace=id)

    def fill_slot(self, id: str, svg_string: str) -> etree._Element:
        """Fill an anchor group with SVG content at the content's own physical size.

        The target is a group translated to an anchor point -- typically a
        VecView ``Scene.slot`` -- whose ``data-align`` names the point of the
        content's box that sits on the anchor (``center`` when absent).  The
        content keeps the size its document declares however the enclosing
        scene was scaled to fit its panel: an 8 pt label stays 8 pt.  The
        anchor itself moves with the scene.

        Returns the wrapping group holding the imported content.
        """
        targets = self.select(f"#{id}")
        if len(targets) == 0:
            raise KeyError(f"No element with id {id!r} in document")
        target = targets.nodes[0]

        align = target.get("data-align", "center")
        if align not in SLOT_ALIGN:
            raise ValueError(
                f"Slot {id!r} has unknown data-align {align!r}; "
                f"expected one of {sorted(SLOT_ALIGN)}"
            )
        view_w, view_h, min_x, min_y = svg_intrinsic_size(svg_string)
        width, height = svg_physical_size(svg_string)
        if not (view_w and view_h and width and height):
            raise ValueError(f"Content for {id!r} has no intrinsic size to place")

        fx, fy = SLOT_ALIGN[align]
        shift = f" translate({-min_x:g} {-min_y:g})" if (min_x or min_y) else ""
        transform = (
            f"scale({1 / accumulated_scale(target):g})"
            f" translate({-fx * width:g} {-fy * height:g})"
            f" scale({width / view_w:g} {height / view_h:g}){shift}"
        )
        return self.import_svg(svg_string, transform=transform, parent=target, namespace=id)

    def place(
        self,
        svg_string: str,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        id: str | None = None,
        preserve_aspect_ratio: bool = True,
        parent: etree._Element | None = None,
    ) -> etree._Element:
        """Place SVG content directly in a layout box."""
        transform = fit_transform(
            (x, y, width, height),
            svg_intrinsic_size(svg_string),
            preserve_aspect_ratio=preserve_aspect_ratio,
        )
        return self.import_svg(svg_string, id=id, transform=transform, parent=parent)

    def _place_in_placeholder(
        self,
        target: etree._Element,
        box: tuple[float, float, float, float],
        svg_string: str,
        preserve_aspect_ratio: bool = True,
    ) -> etree._Element:
        x, y, w, h = box
        parent = target.getparent()
        if parent is None:
            parent = self.root
        index = list(parent).index(target)
        parent.remove(target)

        transform = fit_transform(
            (x, y, w, h),
            svg_intrinsic_size(svg_string),
            preserve_aspect_ratio=preserve_aspect_ratio,
        )

        group = self.import_svg(svg_string, namespace=target.get("id"))
        if not preserve_aspect_ratio:
            group.set("preserveAspectRatio", "none")
        parent.insert(index, group)
        group.set("transform", transform)
        return group

    def select(self, selector: str) -> Selection:
        return select(self.root, selector)

    def delete(self, selector: str) -> Selection:
        return self.select(selector).delete()

    def set_style(self, selector: str, **style: str | int | float) -> Selection:
        return self.select(selector).set_style(**style)

    def to_string(self) -> str:
        return etree.tostring(
            self.root,
            encoding="unicode",
            pretty_print=True,
            xml_declaration=False,
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_string(), encoding="utf-8")


def extract_path_box(node: etree._Element) -> tuple[float, float, float, float]:
    """Estimate a bounding box (x, y, w, h) from a node's path data."""
    d = node.get("d", "") or node.get("points", "")
    xs: list[float] = []
    ys: list[float] = []
    a1, a2 = xs, ys
    for token in d.split():
        try:
            a1.append(float(token))
            a1, a2 = a2, a1
        except ValueError:
            continue
    if not xs or not ys:
        return 0.0, 0.0, 0.0, 0.0
    min_x, min_y = min(xs), min(ys)
    return min_x, min_y, max(xs) - min_x, max(ys) - min_y


def element_box(node: etree._Element) -> tuple[float, float, float, float]:
    """Return (x, y, width, height) for an element's layout box."""
    name = etree.QName(node).localname
    if name in {"image", "rect"}:
        x = float(node.get("x", 0.0))
        y = float(node.get("y", 0.0))
        w = float(node.get("width", 0.0))
        h = float(node.get("height", 0.0))
        return x, y, w, h
    if name in ("path", "polyline"):
        return extract_path_box(node)
    if name == "g":
        boxes = [element_box(child) for child in node]
        boxes = [box for box in boxes if box[2] and box[3]]
        if boxes:
            min_x = min(box[0] for box in boxes)
            min_y = min(box[1] for box in boxes)
            max_x = max(box[0] + box[2] for box in boxes)
            max_y = max(box[1] + box[3] for box in boxes)
            return min_x, min_y, max_x - min_x, max_y - min_y
    return 0.0, 0.0, 0.0, 0.0
