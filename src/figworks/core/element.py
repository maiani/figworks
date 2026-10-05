"""Shared low-level SVG/XML helpers and element primitives.

This module is the canonical home for helpers that construct, parse, size, and
place SVG content. Higher-level modules (:mod:`figworks.core.document`,
:mod:`figworks.matplotlib`) build on these primitives.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields
from pathlib import Path
from typing import Any

import svg
from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"


def svg_tag(name: str) -> str:
    """Return a fully-namespaced tag name for an SVG element."""
    return f"{{{SVG_NS}}}{name}"


def local_name(node: etree._Element) -> str:
    """Return the local (unprefixed) element name."""
    return etree.QName(node).localname


def parse_svg(svg_string: str, *, recover: bool = True) -> etree._Element:
    """Parse an SVG string into an lxml element tree."""
    parser = etree.XMLParser(remove_blank_text=True, recover=recover)
    return etree.fromstring(svg_string.encode("utf-8"), parser=parser)


def _attr_name(field: str) -> str:
    """Map an svg.py field name to its attribute name, as svg.py does."""
    return field.rstrip("_").replace("__", ":").replace("_", "-")


def svg_to_lxml(
    element: svg.Element,
    *,
    raw: Mapping[str, str | None] | None = None,
) -> etree._Element:
    """Render an svg.py element and parse it into an lxml node.

    ``raw`` sets pre-formatted strings for fields svg.py types structurally
    (``transform``, path ``d``, polyline ``points``), keyed by svg.py field name.
    They land where svg.py would have written them, so attribute order matches.
    """
    node = parse_svg(str(element), recover=False)
    for descendant in node.iter():
        if not isinstance(descendant.tag, str):
            continue
        name = etree.QName(descendant)
        if name.namespace is None:
            descendant.tag = svg_tag(name.localname)

    values = {_attr_name(key): value for key, value in (raw or {}).items() if value is not None}
    if values:
        rank = {_attr_name(field.name): index for index, field in enumerate(fields(element))}
        existing = list(node.attrib.items())
        # svg.py writes typed fields first, in field order, then data/extra attributes.
        field_count = len(element.as_dict())
        head = [(str(key), str(value)) for key, value in existing[:field_count]]
        head = sorted([*head, *values.items()], key=lambda item: rank.get(item[0], len(rank)))
        tail = [(str(key), str(value)) for key, value in existing[field_count:]]
        node.attrib.clear()
        for key, value in [*head, *tail]:
            node.set(key, value)
    return node


def svg_kwargs(attrs: dict[str, Any]) -> dict[str, Any]:
    """Drop empty (``None``) values before passing attrs to svg.py constructors."""
    return {key: value for key, value in attrs.items() if value is not None}


def register_ns(root: etree._Element | None = None) -> None:
    """Register the SVG namespace under the default prefix when unbound.

    Calling this is safe even when a default namespace is already declared;
    lxml rejects re-registering a prefix that any element already uses.
    """
    if root is None or root.nsmap.get(None) != SVG_NS:
        etree.register_namespace("", SVG_NS)


def ensure_defs(root: etree._Element) -> etree._Element:
    """Return the root's ``<defs>`` element, creating it if needed."""
    existing = root.find(svg_tag("defs"))
    if existing is not None:
        return existing
    defs = svg_to_lxml(svg.Defs())
    root.insert(0, defs)
    return defs


def copy_element(child: etree._Element) -> etree._Element:
    """Deep-copy a single lxml element into a detached tree."""
    return deepcopy(child)


_XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def _unique(candidate: str, taken: set[str]) -> str:
    """``candidate``, or ``candidate-2``, ``candidate-3``... if already taken."""
    name, n = candidate, 1
    while name in taken:
        n += 1
        name = f"{candidate}-{n}"
    return name


def _rewrite_references(root: etree._Element, renamed: dict[str, str]) -> None:
    """Point every ``url(#id)`` and ``href="#id"`` inside ``root`` at the renamed ids."""
    if not renamed:
        return
    pattern = re.compile(
        r"url\(\s*(['\"]?)#(" + "|".join(re.escape(old) for old in renamed) + r")\1\s*\)"
    )

    def swap(match: re.Match[str]) -> str:
        quote = match.group(1)
        return f"url({quote}#{renamed[match.group(2)]}{quote})"

    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        for key, value in node.attrib.items():
            if not isinstance(value, str):
                continue
            if key in ("href", _XLINK_HREF) and value.startswith("#") and value[1:] in renamed:
                node.set(key, "#" + renamed[value[1:]])
            elif "url(" in value:
                node.set(key, pattern.sub(swap, value))
        if local_name(node) == "style" and node.text and "url(" in node.text:
            node.text = pattern.sub(swap, node.text)


def _canonical(node: etree._Element) -> bytes:
    """Serialization that ignores inherited namespace declarations and tail text."""
    return etree.tostring(node, method="c14n", exclusive=True, with_tail=False)


def resolve_id_collisions(
    fragment: etree._Element, document: etree._Element, namespace: str
) -> set[etree._Element]:
    """Rename ids in ``fragment`` that already exist in ``document``, in place.

    An id that does not collide is kept, so ids survive placement in the common
    case.  A colliding id becomes ``{namespace}-{id}`` (suffixed further if that
    is taken too), and every reference to it inside the fragment follows.  A
    colliding definition identical to the document's own is not renamed but
    returned, so the caller can drop it and let both share one definition.
    """
    existing = {key: node for node in document.iter() if (key := node.get("id"))}
    # A new name must avoid the fragment's own ids as well as the document's.
    taken = set(existing) | {key for node in fragment.iter() if (key := node.get("id"))}
    duplicates: set[etree._Element] = set()
    renamed: dict[str, str] = {}
    for node in fragment.iter():
        old = node.get("id")
        if not old or old not in existing:
            continue
        parent = node.getparent()
        if (
            parent is not None
            and local_name(parent) == "defs"
            and _canonical(node) == _canonical(existing[old])
        ):
            duplicates.add(node)
            continue
        new = _unique(f"{namespace}-{old}", taken)
        taken.add(new)
        renamed[old] = new
        node.set("id", new)
    _rewrite_references(fragment, renamed)
    return duplicates


def svg_intrinsic_size(svg_string: str) -> tuple[float, float, float, float]:
    """Return (width, height, min_x, min_y) of an SVG string."""
    root = parse_svg(svg_string)
    view_box = root.get("viewBox")
    if view_box:
        min_x, min_y, width, height = [float(value) for value in view_box.replace(",", " ").split()]
        return width, height, min_x, min_y
    from figworks.core.units import to_px

    width = to_px(root.get("width", "1px"))
    height = to_px(root.get("height", "1px"))
    return width, height, 0.0, 0.0


def svg_physical_size(svg_string: str) -> tuple[float, float]:
    """Return the (width, height) an SVG document asks to be drawn at, in px.

    Taken from the root's ``width``/``height`` with their units, falling back to
    the viewBox extents when either is missing.
    """
    from figworks.core.units import to_px

    root = parse_svg(svg_string)
    view_w, view_h, _, _ = svg_intrinsic_size(svg_string)
    width, height = root.get("width"), root.get("height")
    return (
        to_px(width) if width is not None else view_w,
        to_px(height) if height is not None else view_h,
    )


_TRANSFORM_RE = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")


def accumulated_scale(node: etree._Element) -> float:
    """Document px per user unit inside ``node``, from every ancestor transform.

    The linear part of a transform chain scales area by the product of each
    function's determinant, so the uniform scale is its square root. That is
    exact for the translate/uniform-scale chains FigWorks writes, and the mean
    scale for anything else. The document root's viewBox is 1:1 by construction.
    """
    det = 1.0
    current: etree._Element | None = node
    while current is not None:
        for name, args in _TRANSFORM_RE.findall(current.get("transform", "")):
            values = [float(value) for value in args.replace(",", " ").split()]
            if name == "scale":
                det *= values[0] * (values[1] if len(values) > 1 else values[0])
            elif name == "matrix":
                det *= values[0] * values[3] - values[1] * values[2]
        current = current.getparent()
    return math.sqrt(abs(det))


def fit_transform(
    box: tuple[float, float, float, float],
    intrinsic: tuple[float, float, float, float],
    *,
    preserve_aspect_ratio: bool = True,
) -> str:
    """Build a transform that fits ``intrinsic`` content inside ``box``.

    ``box`` is ``(x, y, width, height)`` and ``intrinsic`` is the result of
    :func:`svg_intrinsic_size`. When aspect ratio is preserved the content is
    scaled uniformly and centered; otherwise it is stretched to fill the box.
    """
    x, y, width, height = box
    src_w, src_h, min_x, min_y = intrinsic

    if src_w and src_h and width and height and preserve_aspect_ratio:
        scale = min(width / src_w, height / src_h)
        dx = x + (width - src_w * scale) / 2
        dy = y + (height - src_h * scale) / 2
        shift = f" translate({-min_x:g} {-min_y:g})" if (min_x or min_y) else ""
        return f"translate({dx:g} {dy:g}) scale({scale:g}){shift}"
    if src_w and src_h and width and height:
        scale_x = width / src_w
        scale_y = height / src_h
        return f"translate({x:g} {y:g}) scale({scale_x:g} {scale_y:g})"
    return f"translate({x:g} {y:g})"


def resolve_svg_source(source: Any) -> str:
    """Resolve an SVG document, Matplotlib figure, path, or SVG string.

    SVG-producing libraries can integrate without a FigWorks adapter by
    exposing ``to_svg_document()``.  VecTeX fragments implement this small
    protocol directly.
    """
    to_svg_document = getattr(source, "to_svg_document", None)
    if callable(to_svg_document):
        document = to_svg_document()
        if not isinstance(document, str):
            raise TypeError("to_svg_document() must return an SVG string")
        return document

    import matplotlib as mpl

    from figworks.matplotlib import mpl_to_svg

    if isinstance(source, mpl.figure.Figure):
        return mpl_to_svg(source)
    if isinstance(source, str):
        stripped = source.lstrip()
        if stripped.startswith("<svg") or stripped.startswith("<?xml"):
            return source
        path = Path(source)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return source
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    raise TypeError("Expected an SVG document provider, Matplotlib figure, SVG path, or SVG string")
