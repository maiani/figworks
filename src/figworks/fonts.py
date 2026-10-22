"""Check, before rendering, that every font a figure asks for is really there.

A missing family is not an error to a renderer: fontconfig substitutes the
closest match, and a missing glyph becomes a box, both silently.  CairoSVG goes
further and honours only the *first* family of a ``font-family`` list, never
the fallbacks.  So a PDF or PNG can quietly come out in the wrong typeface, and
differently on another machine, while the SVG it was rendered from is
byte-identical.  :func:`check_fonts` makes that an error instead.

The CSS ``font`` shorthand, which Matplotlib before 3.10 writes for every run of
text (``style="font: italic 8px 'cmex10'"``), needs care.  CairoSVG fills in a
shorthand's parts only where the node has no such property yet, *inherited ones
included*, so under a root that sets ``font-family`` -- every FigWorks figure --
it ignores the shorthand's family and draws the run in the root's face.  A glyph
code meant for one font then prints as an unrelated character of another.
:func:`expand_font_shorthand` rewrites shorthands as the longhand properties
CSS defines them as, which CairoSVG honours, and both the check and FigWorks'
PDF and PNG export apply it first, so they agree with each other and with the
SVG as a browser shows it.
"""

from __future__ import annotations

import re
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

# The CSS Fonts grammar of the ``font`` shorthand, up to its size:
# [ <style> || <variant> || <weight> || <stretch> ]? <size> [ / <line-height> ]? <family>#
_FONT_STYLES = frozenset({"italic", "oblique"})
_FONT_VARIANTS = frozenset({"small-caps"})
_FONT_WEIGHTS = frozenset({"bold", "bolder", "lighter"})
_FONT_STRETCHES = frozenset(
    {
        "ultra-condensed",
        "extra-condensed",
        "condensed",
        "semi-condensed",
        "semi-expanded",
        "expanded",
        "extra-expanded",
        "ultra-expanded",
    }
)
_FONT_SIZES = frozenset(
    {
        "xx-small",
        "x-small",
        "small",
        "medium",
        "large",
        "x-large",
        "xx-large",
        "xxx-large",
        "larger",
        "smaller",
    }
)
_UNSIGNED = r"(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?"
_NUMBER = rf"[+]?{_UNSIGNED}"
_SIZE = re.compile(rf"(?:{_NUMBER}(?:[a-z]+|%)|[+]?0*\.?0+)", re.IGNORECASE)
_LINE_HEIGHT = re.compile(rf"(?:{_NUMBER}(?:[a-z]+|%)?|normal)", re.IGNORECASE)
_WEIGHT = re.compile(r"\d+(?:\.\d+)?")
_ANGLE = re.compile(rf"[+-]?{_UNSIGNED}deg", re.IGNORECASE)
_FONT_DECLARATION = re.compile(r"(?:^|;)\s*font\s*:", re.IGNORECASE)


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


def parse_font_shorthand(value: str) -> dict[str, str] | None:
    """The longhand properties a CSS ``font`` shorthand sets, or ``None`` if invalid.

    Follows the CSS Fonts grammar: optional style, variant, weight, and stretch
    keywords in any order, then the size, an optional ``/line-height``, and the
    family list, kept as written.  Every property it omits is reset to
    ``normal``, as in CSS.  System fonts (``font: caption``) and values with
    functions such as ``calc()`` are not resolved and return ``None``::

        >>> parse_font_shorthand("italic 5.6px 'TeX Gyre Heros'")["font-style"]
        'italic'
    """
    found: dict[str, str] = {}
    keywords = 0
    for match in re.finditer(r"\S+", value):
        word = match.group().lower()
        if "(" in word or word[0] in "'\"":
            return None
        if found.get("font-style") == "oblique" and _ANGLE.fullmatch(word):
            continue  # ``oblique 10deg``: the angle does not change the face
        size, slash, line_height = word.partition("/")
        if _SIZE.fullmatch(size) or size in _FONT_SIZES:
            rest = value[match.end() :]
            if not slash and rest.lstrip().startswith("/"):
                slash, rest = "/", rest.lstrip()[1:]
            if slash and not line_height:
                parts = rest.split(None, 1)
                line_height, rest = (parts[0], parts[1]) if len(parts) == 2 else ("", "")
            family = rest.strip()
            if (slash and not _LINE_HEIGHT.fullmatch(line_height)) or not family:
                return None
            if family.endswith(",") or ",," in family.replace(" ", ""):
                return None
            return {
                "font-style": found.get("font-style", "normal"),
                "font-variant": found.get("font-variant", "normal"),
                "font-weight": found.get("font-weight", "normal"),
                "font-stretch": found.get("font-stretch", "normal"),
                "font-size": size,
                "line-height": line_height if slash else "normal",
                "font-family": family,
            }
        keywords += 1
        if keywords > 4:
            return None
        if word == "normal":
            continue
        for name, words in (
            ("font-style", _FONT_STYLES),
            ("font-variant", _FONT_VARIANTS),
            ("font-weight", _FONT_WEIGHTS),
            ("font-stretch", _FONT_STRETCHES),
        ):
            if word in words and name not in found:
                found[name] = word
                break
        else:
            if "font-weight" not in found and _WEIGHT.fullmatch(word) and 1 <= float(word) <= 1000:
                found["font-weight"] = word
            else:
                return None
    return None


def style_declarations(style: str) -> list[tuple[str, str]]:
    """The ``name: value`` pairs of a ``style`` attribute, in order."""
    pairs = []
    for declaration in style.split(";"):
        key, _, value = declaration.partition(":")
        if key.strip() and value.strip():
            pairs.append((key.strip().lower(), value.strip()))
    return pairs


def expand_font_shorthand(root: etree._Element) -> list[str]:
    """Rewrite every CSS ``font`` shorthand under ``root`` as longhands, in place.

    A shorthand in ``style`` becomes the longhand declarations it stands for, at
    its own position, so declarations after it still override it, as in CSS.
    ``font`` is not an SVG presentation attribute and browsers ignore it, so a
    ``font=`` attribute is removed rather than left for CairoSVG to apply.
    Returns the shorthand values that could not be read; they are left as they
    are, and :func:`check_fonts` reports them.
    """
    unreadable = []
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        if "font" in node.attrib:
            del node.attrib["font"]
        style = node.get("style")
        if not style or not _FONT_DECLARATION.search(style):
            continue
        pairs: list[tuple[str, str]] = []
        for name, value in style_declarations(style):
            longhand = parse_font_shorthand(value) if name == "font" else None
            if name == "font" and longhand is None:
                unreadable.append(value)
            pairs.extend(longhand.items() if longhand else [(name, value)])
        node.set("style", "; ".join(f"{name}: {value}" for name, value in pairs))
    return unreadable


def for_cairosvg(svg_string: str) -> str:
    """``svg_string`` with its ``font`` shorthands expanded, ready for CairoSVG."""
    if "font" not in svg_string or not re.search(r"font\s*[:=]", svg_string):
        return svg_string
    root = parse_svg(svg_string)
    expand_font_shorthand(root)
    return etree.tostring(root, encoding="unicode")


def _style_value(node: etree._Element, name: str) -> str | None:
    """A property set on ``node``: the last declaration in ``style``, else the attribute."""
    for key, value in reversed(style_declarations(node.get("style") or "")):
        if key == name:
            return value
    attribute = node.get(name)
    return attribute.strip() if attribute else None


def _faces_and_text(root: etree._Element) -> Iterator[tuple[Face, str]]:
    """Each run of text with the face it is drawn in, as CairoSVG resolves it.

    Expects shorthands already expanded by :func:`expand_font_shorthand`.
    """
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


def _is_bold(weight: str) -> bool:
    """CairoSVG's two weights: ``bold``, or a number of 550 and up, is bold."""
    weight = weight.strip().lower()
    return weight == "bold" or (bool(_WEIGHT.fullmatch(weight)) and float(weight) >= 550)


def _fontconfig_pattern(face: Face) -> str:
    weight = "bold" if _is_bold(face.weight) else "regular"
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
    The CSS ``font`` shorthand counts as the longhands it stands for, as FigWorks
    renders it (see :func:`expand_font_shorthand`); one that cannot be read is
    a problem.  A generic family (``sans-serif``) resolves differently on every
    machine, so it is reported too.  All problems are collected into one error.
    """
    root = parse_svg(svg_string)
    problems = [
        f"font: {value}: cannot read this CSS font shorthand; "
        "set font-family, font-size, font-style, and font-weight instead"
        for value in expand_font_shorthand(root)
    ]
    used: dict[Face, set[str]] = {}
    for face, text in _faces_and_text(root):
        chars = {char for char in text if not char.isspace()}
        if chars:
            used.setdefault(face, set()).update(chars)

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


__all__ = [
    "GENERIC_FAMILIES",
    "Face",
    "FontError",
    "ResolvedFace",
    "check_fonts",
    "expand_font_shorthand",
    "for_cairosvg",
    "parse_font_shorthand",
]
