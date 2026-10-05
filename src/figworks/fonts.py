"""Check, before rendering, that every font a figure asks for is really there.

A missing family is not an error to a renderer: fontconfig substitutes the
closest match, and a missing glyph becomes a box, both silently.  CairoSVG goes
further and honours only the *first* family of a ``font-family`` list, never
the fallbacks.  So a PDF or PNG can quietly come out in the wrong typeface, and
differently on another machine, while the SVG it was rendered from is
byte-identical.  :func:`check_fonts` makes that an error instead.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cache

from lxml import etree

from figworks.core.element import local_name, parse_svg

GENERIC_FAMILIES = frozenset(
    {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
)
_TEXT_ELEMENTS = frozenset({"text", "tspan", "textPath"})
_INHERITED = ("font-family", "font-weight", "font-style")


class FontError(ValueError):
    """A figure asks for a font, or a glyph, that this machine cannot render."""


@dataclass(frozen=True)
class Face:
    """The face a renderer would use for one family, weight, and style."""

    family: str
    weight: str
    style: str


@dataclass(frozen=True)
class ResolvedFace:
    """What fontconfig actually chose: the file, its real families, its coverage."""

    file: str
    families: tuple[str, ...]
    codepoints: tuple[tuple[int, int], ...]

    def covers(self, char: str) -> bool:
        """Whether ``char`` falls in one of the face's code-point ranges."""
        code = ord(char)
        return any(lo <= code <= hi for lo, hi in self.codepoints)


type Resolver = Callable[[Face], ResolvedFace | None]


def _style_value(node: etree._Element, name: str) -> str | None:
    """A presentation attribute or the same property in ``style``, if set on ``node``."""
    for declaration in (node.get("style") or "").split(";"):
        key, _, value = declaration.partition(":")
        if key.strip() == name and value.strip():
            return value.strip()
    attribute = node.get(name)
    return attribute.strip() if attribute else None


def _faces_and_text(root: etree._Element) -> Iterator[tuple[Face, str]]:
    """Each run of text with the face it is drawn in, as CairoSVG resolves it."""
    stack: list[dict[str, str]] = [
        {"font-family": "sans-serif", "font-weight": "normal", "font-style": "normal"}
    ]

    def walk(node: etree._Element) -> Iterator[tuple[Face, str]]:
        if not isinstance(node.tag, str):
            return
        props = dict(stack[-1])
        for name in _INHERITED:
            value = _style_value(node, name)
            if value and value != "inherit":
                props[name] = value
        stack.append(props)
        family = props["font-family"].split(",")[0].strip().strip("'\"")
        face = Face(family, props["font-weight"], props["font-style"])
        in_text = local_name(node) in _TEXT_ELEMENTS
        if in_text and node.text:
            yield face, node.text
        for child in node:
            yield from walk(child)
            if in_text and isinstance(child.tag, str) and child.tail:
                yield face, child.tail
        stack.pop()

    yield from walk(root)


def _fontconfig_pattern(face: Face) -> str:
    weight = "bold" if face.weight in ("bold", "bolder", "600", "700", "800", "900") else "regular"
    slant = {"italic": "italic", "oblique": "oblique"}.get(face.style, "roman")
    return f"{face.family}:weight={weight}:slant={slant}"


def _parse_charset(charset: str) -> tuple[tuple[int, int], ...]:
    ranges = []
    for token in charset.split():
        lo, _, hi = token.partition("-")
        ranges.append((int(lo, 16), int(hi or lo, 16)))
    return tuple(ranges)


@cache
def fontconfig_resolver(face: Face) -> ResolvedFace | None:
    """Resolve ``face`` the way CairoSVG will, reading the chosen file afresh.

    The family and coverage come from ``fc-query`` on the matched file rather
    than from ``fc-match``'s report, which echoes the requested family back and
    can carry a stale cache entry's empty character set.
    """
    match, query = shutil.which("fc-match"), shutil.which("fc-query")
    if match is None or query is None:
        raise FontError(
            "cannot check fonts: fontconfig's fc-match and fc-query were not found. "
            "Install fontconfig's command-line tools."
        )
    found = subprocess.run(
        [match, "--format=%{file}\t%{index}", _fontconfig_pattern(face)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    if "\t" not in found:
        return None
    file, index = found.split("\t", 1)
    info = subprocess.run(
        [query, "--index", index or "0", "--format=%{family}\t%{charset}", file],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    families, _, charset = info.partition("\t")
    return ResolvedFace(
        file=file,
        families=tuple(name.strip() for name in families.split(",") if name.strip()),
        codepoints=_parse_charset(charset),
    )


def check_fonts(svg_string: str, resolve: Resolver = fontconfig_resolver) -> None:
    """Raise :class:`FontError` unless every text run renders in the font it names.

    Checks the first family of each run's inherited ``font-family`` -- the only
    one CairoSVG uses -- with its weight and style: that the face resolves to a
    file of that family, and that the file covers every character drawn in it.
    A generic family (``sans-serif``) resolves differently on every machine, so
    it is reported too.  All problems are collected into one error.
    """
    root = parse_svg(svg_string)
    used: dict[Face, set[str]] = {}
    for face, text in _faces_and_text(root):
        chars = {char for char in text if not char.isspace()}
        if chars:
            used.setdefault(face, set()).update(chars)

    problems = []
    for face, chars in sorted(used.items(), key=lambda item: _fontconfig_pattern(item[0])):
        label = _fontconfig_pattern(face)
        if face.family.lower() in GENERIC_FAMILIES:
            problems.append(
                f"{label}: a generic family renders differently per machine; name a font"
            )
            continue
        resolved = resolve(face)
        if resolved is None or face.family.lower() not in {f.lower() for f in resolved.families}:
            got = (
                "nothing"
                if resolved is None
                else f"{', '.join(resolved.families)} ({resolved.file})"
            )
            problems.append(f"{label}: not installed; it would render as {got}")
            continue
        missing = sorted(char for char in chars if not resolved.covers(char))
        if missing:
            shown = " ".join(f"{char!r} U+{ord(char):04X}" for char in missing)
            problems.append(f"{label}: no glyph for {shown} in {resolved.file}")
    if problems:
        raise FontError("this figure would not render as written:\n  " + "\n  ".join(problems))


__all__ = ["GENERIC_FAMILIES", "Face", "FontError", "ResolvedFace", "check_fonts"]
