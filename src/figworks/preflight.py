"""Conservative, read-only publication checks on the assembled SVG."""

from __future__ import annotations

import base64
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from typing import Literal
from urllib.parse import unquote_to_bytes

from lxml import etree

from figworks.core.element import _references, local_name
from figworks.core.units import to_px
from figworks.fonts import FontError, Resolver, check_fonts, fontconfig_resolver

Severity = Literal["error", "warning", "info"]
Matrix = tuple[float, float, float, float, float, float]
_IDENTITY: Matrix = (1, 0, 0, 1, 0, 0)
_TRANSFORM = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")
_NUMBER = re.compile(r"[+-]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][+-]?\d+)?")
_URL = re.compile(r"url\(\s*['\"]?([^)'\"]+)")
_NONPAINT = {
    "defs",
    "metadata",
    "title",
    "desc",
    "clipPath",
    "mask",
    "symbol",
    "pattern",
    "marker",
    "linearGradient",
    "radialGradient",
}
_SHAPES = {"rect", "image", "circle", "ellipse", "line", "polyline", "polygon", "path", "use"}


@dataclass(frozen=True)
class CheckIssue:
    """One finding, identified by a stable code and an SVG element location."""

    severity: Severity
    code: str
    message: str
    element_id: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class CheckReport:
    """Findings and explicit coverage limits; ``ok`` means no reported errors."""

    issues: tuple[CheckIssue, ...]
    unchecked: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def summary(self) -> str:
        """One-line counts; detailed findings and coverage remain on the report."""
        errors = sum(issue.severity == "error" for issue in self.issues)
        warnings = sum(issue.severity == "warning" for issue in self.issues)
        notes = sum(issue.severity == "info" for issue in self.issues)
        return (
            f"{errors} errors, {warnings} warnings, {notes} notes; "
            f"{len(self.unchecked)} unchecked areas"
        )

    def raise_for_errors(self) -> None:
        """Raise only for definite errors, leaving warning policy to the caller."""
        errors = [issue.message for issue in self.issues if issue.severity == "error"]
        if errors:
            raise ValueError("Figure preflight failed:\n" + "\n".join(errors))


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    a, b, c, d, e, f = left
    g, h, i, j, k, offset_y = right
    return (
        a * g + c * h,
        b * g + d * h,
        a * i + c * j,
        b * i + d * j,
        a * k + c * offset_y + e,
        b * k + d * offset_y + f,
    )


def _matrix(value: str) -> Matrix:
    result = _IDENTITY
    end = 0
    for match in _TRANSFORM.finditer(value):
        if value[end : match.start()].strip(" ,\t\n"):
            raise ValueError("unsupported transform")
        name, args = match.groups()
        values = [float(number) for number in _NUMBER.findall(args)]
        if _NUMBER.sub("", args).strip(" ,\t\n") or not all(map(math.isfinite, values)):
            raise ValueError("unsupported transform arguments")
        if name == "matrix" and len(values) == 6:
            transform = tuple(values)
        elif name == "translate" and len(values) in (1, 2):
            transform = (1, 0, 0, 1, values[0], values[1] if len(values) == 2 else 0)
        elif name == "scale" and len(values) in (1, 2):
            transform = (values[0], 0, 0, values[-1], 0, 0)
        elif name == "rotate" and len(values) in (1, 3):
            angle = math.radians(values[0])
            cosine, sine = math.cos(angle), math.sin(angle)
            transform = (cosine, sine, -sine, cosine, 0, 0)
            if len(values) == 3:
                x, y = values[1:]
                transform = _multiply(
                    _multiply((1, 0, 0, 1, x, y), transform), (1, 0, 0, 1, -x, -y)
                )
        elif name in ("skewX", "skewY") and len(values) == 1:
            skew = math.tan(math.radians(values[0]))
            transform = (1, 0, skew, 1, 0, 0) if name == "skewX" else (1, skew, 0, 1, 0, 0)
        else:
            raise ValueError("unsupported transform")
        result = _multiply(result, transform)  # ty: ignore[invalid-argument-type]
        end = match.end()
    if value[end:].strip(" ,\t\n"):
        raise ValueError("unsupported transform")
    return result


def _scales(matrix: Matrix) -> tuple[float, float]:
    a, b, c, d, _, _ = matrix
    total = a * a + b * b + c * c + d * d
    delta = math.sqrt(max(0, total * total - 4 * (a * d - b * c) ** 2))
    return math.sqrt(max(0, (total - delta) / 2)), math.sqrt(max(0, (total + delta) / 2))


def _length(value: str) -> float:
    number = to_px(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite length")
    return number


# Matplotlib's mathtext, like TeX, sets a first-level sub- or superscript at
# 0.7 of its label: a 7 pt label has 4.9 pt scripts, which no label size can
# avoid within a 5-7 pt range, so those are noted rather than warned about.
_SCRIPT = 0.7 * (1 - 1e-6)


def _script_base(node: etree._Element, inherited: dict[str, str]) -> float:
    """The largest run in a ``<tspan>``'s own ``<text>``, in px; 0 for anything else."""
    parent = node.getparent()
    if local_name(node) != "tspan" or parent is None or local_name(parent) != "text":
        return 0.0
    runs = [run for run in parent if isinstance(run.tag, str) and local_name(run) == "tspan"]
    return max(_length(_properties(run, inherited).get("font-size", "16")) for run in runs)


def _properties(node: etree._Element, inherited: dict[str, str]) -> dict[str, str]:
    props = dict(inherited)
    for key in ("font-size", "stroke", "stroke-width", "visibility", "fill"):
        if node.get(key) is not None:
            props[key] = node.get(key, "")
    for part in node.get("style", "").split(";"):
        key, _, value = part.partition(":")
        if value.strip() and value.strip() != "inherit":
            props[key.strip()] = value.strip()
    return props


def _measurement_stylesheet(node: etree._Element) -> bool:
    """Ignore only universal cap/join rules, as emitted by Matplotlib.

    They affect neither fonts nor scale; simple-shape bounds already include
    conservative cap/join padding. All other stylesheet rules remain unknown.
    """
    match = re.fullmatch(r"\s*\*\s*\{([^{}]*)\}\s*", node.text or "")
    if match is None:
        return True
    declarations = [part.strip() for part in match[1].split(";") if part.strip()]
    allowed = {
        "stroke-linejoin": {"round", "miter", "bevel"},
        "stroke-linecap": {"butt", "round", "square"},
    }
    for declaration in declarations:
        name, _, value = declaration.partition(":")
        if value.strip() not in allowed.get(name.strip(), set()):
            return True
    return False


def check_document(
    root: etree._Element,
    *,
    target: Literal["svg", "pdf", "png"] = "pdf",
    min_font_pt: float = 6,
    min_stroke_pt: float = 0.25,
    min_raster_dpi: float = 300,
    resolve_fonts: Resolver = fontconfig_resolver,
) -> CheckReport:
    """Inspect without rendering, fetching resources, or changing the document.

    Measurements support presentation attributes, inline styles, and affine
    transforms. Stylesheets, CSS transforms, nested viewports, complex bounds,
    and referenced geometry are explicitly left unchecked. Thresholds are
    publication heuristics, not journal requirements; zero disables a threshold.
    """
    if target not in {"svg", "pdf", "png"}:
        raise ValueError("target must be 'svg', 'pdf', or 'png'")
    for value in (min_font_pt, min_stroke_pt, min_raster_dpi):
        if not math.isfinite(value) or value < 0:
            raise ValueError("thresholds must be finite and nonnegative")
    issues: list[CheckIssue] = []
    unchecked: set[str] = set()
    tree = root.getroottree()

    def issue(severity: Severity, code: str, message: str, node: etree._Element = root) -> None:
        # Keep the precise XPath while naming the nearest authored group.
        owner = next(
            (item.get("id") for item in (node, *node.iterancestors()) if item.get("id")), None
        )
        issues.append(CheckIssue(severity, code, message, owner, tree.getpath(node)))

    nodes = [node for node in root.iter() if isinstance(node.tag, str)]
    ids: set[str] = set()
    css = any(local_name(node) == "style" and _measurement_stylesheet(node) for node in nodes)
    shorthand = any(re.search(r"(?:^|;)\s*font\s*:", node.get("style", "")) for node in nodes)
    if shorthand:
        unchecked.add("CSS font shorthand: font selection and physical measurements.")
    css = css or shorthand
    for node in nodes:
        if name := node.get("id"):
            if name in ids:
                issue("error", "duplicate-id", f"Duplicate SVG id {name!r}.", node)
            ids.add(name)
    for ref in sorted(_references(root) - ids):
        issue("error", "broken-reference", f"Reference #{ref} has no target.")
    for node in nodes:
        tag = local_name(node)
        if (
            tag
            in {"foreignObject", "filter", "animate", "animateTransform", "animateMotion", "set"}
            and target != "svg"
        ):
            issue(
                "warning",
                "export-feature",
                f"{tag} may be omitted or rendered differently by CairoSVG ({target}).",
                node,
            )
        for key, value in node.attrib.items():
            href = etree.QName(key).localname == "href"
            resources = [value] if href and tag != "a" else []
            resources.extend(match.group(1).strip() for match in _URL.finditer(value))
            for resource in resources:
                if resource and not resource.startswith(("#", "data:")):
                    issue(
                        "warning",
                        "external-resource",
                        "External resource is not embedded; it was not fetched.",
                        node,
                    )
        if tag == "style" and _measurement_stylesheet(node):
            unchecked.add("Stylesheets: fonts, sizes, visibility, bounds, and CSS resources.")
        if tag in {"pattern", "marker"}:
            unchecked.add(
                "Fonts, sizes, raster resolution, and bounds inside patterns and markers."
            )
        if tag in {"animate", "animateTransform", "animateMotion", "set", "foreignObject"}:
            unchecked.add("Animated states and foreignObject layout.")
        if tag == "script":
            issue("warning", "script", "Script-dependent output is not evaluated.", node)
    if not css:
        font_root = deepcopy(root)

        def prune_fonts(node: etree._Element, inherited: dict[str, str]) -> None:
            props = _properties(node, inherited)
            hidden = props.get("visibility", node.get("visibility")) in {"hidden", "collapse"}
            if hidden:
                node.text = None
                for child in node:
                    child.tail = None
            for child in list(node):
                if not isinstance(child.tag, str):
                    continue
                child_props = _properties(child, props)
                if (
                    local_name(child) in _NONPAINT
                    or child.get("display") == "none"
                    or child_props.get("display") == "none"
                ):
                    node.remove(child)
                else:
                    prune_fonts(child, {k: v for k, v in props.items() if k == "visibility"})

        prune_fonts(font_root, {})
        try:
            check_fonts(etree.tostring(font_root, encoding="unicode"), resolve=resolve_fonts)
        except FontError as exc:
            issue("error", "font", str(exc))
    try:
        width, height = _length(root.get("width", "")), _length(root.get("height", ""))
        view = [float(x) for x in root.get("viewBox", "").replace(",", " ").split()]
        if (
            len(view) != 4
            or view[2] <= 0
            or view[3] <= 0
            or width <= 0
            or height <= 0
            or not all(map(math.isfinite, view))
        ):
            raise ValueError("invalid viewport")
        sx, sy = width / view[2], height / view[3]
        if not math.isclose(sx, sy, rel_tol=1e-5):
            raise ValueError("nonuniform root viewport")
        initial: Matrix | None = (sx, 0, 0, sy, -view[0] * sx, -view[1] * sy) if not css else None
    except ValueError:
        issue(
            "warning",
            "viewport",
            "Root dimensions/viewBox cannot be resolved to a uniform physical scale.",
        )
        unchecked.add("Physical measurements with a nonmatching root viewport.")
        width = height = 0
        initial = None

    def walk(
        node: etree._Element,
        parent: Matrix | None,
        inherited: dict[str, str],
        clipped: bool = False,
    ) -> None:
        if not isinstance(node.tag, str) or local_name(node) in _NONPAINT:
            return
        tag = local_name(node)
        props = _properties(node, inherited)
        if node.get("display") == "none" or props.get("display") == "none":
            return
        matrix = parent
        if (node is not root and tag == "svg") or "transform" in props:
            matrix = None
            unchecked.add("Nested SVG viewports and CSS transforms.")
        if matrix is not None:
            try:
                matrix = _multiply(matrix, _matrix(node.get("transform", "")))
            except (ValueError, OverflowError):
                matrix = None
                unchecked.add("Unsupported or invalid transforms.")
        clipping = clipped or any(
            node.get(k) or props.get(k) for k in ("clip-path", "mask", "filter")
        )
        visible = props.get("visibility", node.get("visibility")) not in {"hidden", "collapse"}
        if visible and tag in _SHAPES | {"text", "tspan", "textPath"}:
            if matrix is not None:
                low, high = _scales(matrix)
                try:
                    if tag in {"text", "tspan", "textPath"} and (
                        node.text or any(child.tail for child in node)
                    ):
                        size = _length(props.get("font-size", "16")) * low * 72 / 96
                        base = _script_base(node, inherited) * low * 72 / 96
                        if size < min_font_pt and base >= min_font_pt and size >= base * _SCRIPT:
                            issue(
                                "info",
                                "small-script",
                                f"A sub- or superscript is {size:.3g} pt, {size / base:.2g} of "
                                f"its {base:.3g} pt label (threshold {min_font_pt:g} pt).",
                                node,
                            )
                        elif size < min_font_pt:
                            issue(
                                "warning",
                                "small-text",
                                f"Text is as small as {size:.3g} pt after placement "
                                f"(threshold {min_font_pt:g} pt).",
                                node,
                            )
                    if tag in _SHAPES and props.get("stroke", "none") != "none":
                        if node.get("vector-effect") or props.get("vector-effect"):
                            unchecked.add("Stroke measurements with vector-effect.")
                        else:
                            stroke = _length(props.get("stroke-width", "1")) * low * 72 / 96
                            if 0 < stroke < min_stroke_pt:
                                issue(
                                    "warning",
                                    "thin-stroke",
                                    f"Stroke can be {stroke:.3g} pt after placement "
                                    f"(threshold {min_stroke_pt:g} pt).",
                                    node,
                                )
                except ValueError:
                    unchecked.add("Relative, calculated, or unsupported font/stroke lengths.")
                if tag == "image":
                    image_check(node, matrix, high)
                if (
                    tag in {"rect", "image", "circle", "ellipse", "line"}
                    and not clipping
                    and not (node.get("vector-effect") or props.get("vector-effect"))
                ):
                    bounds_check(node, matrix, props, high)
                else:
                    unchecked.add(
                        "Painted bounds for paths, text, use, markers, "
                        "and clipped or filtered content."
                    )
            else:
                unchecked.add("Sizes, raster resolution, and bounds in unmeasurable subtrees.")
            if tag == "image":
                issue(
                    "info",
                    "embedded-image",
                    "Image content may be raster; SVG export does not imply a fully vector figure.",
                    node,
                )
            if tag == "use":
                unchecked.add(
                    "Font/stroke sizes, visibility, raster resolution, and bounds of use instances."
                )
        child_props = {
            k: v
            for k, v in props.items()
            if k in {"font-size", "stroke", "stroke-width", "fill", "visibility"}
        }
        for child in node:
            walk(child, matrix, child_props, clipping)

    def image_check(node: etree._Element, matrix: Matrix, high: float) -> None:
        from PIL import Image, UnidentifiedImageError

        source = node.get("href") or node.get("{http://www.w3.org/1999/xlink}href", "")
        if not source.startswith("data:") or "image/svg+xml" in source.partition(",")[0]:
            unchecked.add("Resolution of external or SVG image resources.")
            return
        try:
            header, payload = source.split(",", 1)
            data = (
                base64.b64decode(payload, validate=True)
                if ";base64" in header
                else unquote_to_bytes(payload)
            )
            with Image.open(BytesIO(data)) as image:
                pixels_x, pixels_y = image.size
            w, h = _length(node.get("width", "")), _length(node.get("height", ""))
            if w <= 0 or h <= 0 or high <= 0:
                raise ValueError("invalid image dimensions")
            aspect = node.get("preserveAspectRatio", "xMidYMid meet").split()
            if not aspect:
                raise ValueError("invalid preserveAspectRatio")
            if aspect[0] == "none":
                a, b, c, d, _, _ = matrix
                pixel_scale = _scales(
                    (a * w / pixels_x, b * w / pixels_x, c * h / pixels_y, d * h / pixels_y, 0, 0)
                )[1]
            else:
                scale = (
                    max(w / pixels_x, h / pixels_y)
                    if "slice" in aspect
                    else min(w / pixels_x, h / pixels_y)
                )
                pixel_scale = high * scale
            dpi = 96 / pixel_scale
            if dpi < min_raster_dpi:
                issue(
                    "warning",
                    "low-resolution",
                    f"Embedded raster has a minimum effective resolution of {dpi:.3g} dpi "
                    f"(threshold {min_raster_dpi:g} dpi).",
                    node,
                )
        except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError):
            issue(
                "warning",
                "image-unreadable",
                "Could not inspect embedded image dimensions; image was not rendered.",
                node,
            )
            unchecked.add("Resolution of unreadable embedded images.")

    def bounds_check(
        node: etree._Element, matrix: Matrix, props: dict[str, str], high: float
    ) -> None:
        def length(key: str, default: str = "0") -> float:
            return _length(node.get(key, default))

        try:
            tag = local_name(node)
            if tag in {"rect", "image"}:
                x, y = length("x"), length("y")
                w, h = length("width"), length("height")
                x2, y2 = x + w, y + h
            elif tag in {"circle", "ellipse"}:
                rx, ry = (
                    (length("r"), length("r")) if tag == "circle" else (length("rx"), length("ry"))
                )
                x, y, x2, y2 = (
                    length("cx") - rx,
                    length("cy") - ry,
                    length("cx") + rx,
                    length("cy") + ry,
                )
            else:
                x, y, x2, y2 = length("x1"), length("y1"), length("x2"), length("y2")
            a, b, c, d, e, f = matrix
            points = [
                (a * u + c * v + e, b * u + d * v + f)
                for u, v in ((x, y), (x, y2), (x2, y), (x2, y2))
            ]
            padding = (
                _length(props.get("stroke-width", "1")) * high / math.sqrt(2)
                if props.get("stroke", "none") != "none"
                else 0
            )
            tolerance = max(1, width, height) * 1e-5
            if any(
                u - padding < -tolerance
                or v - padding < -tolerance
                or u + padding > width + tolerance
                or v + padding > height + tolerance
                for u, v in points
            ):
                issue(
                    "warning",
                    "outside-page",
                    "Conservative geometry/stroke bounds extend outside the page; "
                    "inspect clipping and visibility.",
                    node,
                )
            if any(
                node.get(k) or props.get(k) for k in ("marker-start", "marker-mid", "marker-end")
            ):
                unchecked.add("Bounds of markers and stroke joins/caps.")
        except ValueError:
            unchecked.add("Bounds with relative or unsupported lengths.")

    walk(root, initial, {})
    return CheckReport(tuple(issues), tuple(sorted(unchecked)))
