"""Minimal selector support for FigWorks SVG documents."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from lxml import etree

from figworks.core.element import local_name


def _style_to_dict(style: str | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if not style:
        return values
    for item in style.split(";"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        key = key.strip()
        if key:
            values[key] = value.strip()
    return values


def _dict_to_style(values: dict[str, str]) -> str:
    return "; ".join(f"{key}: {value}" for key, value in values.items())


@dataclass
class Selection:
    """A lightweight wrapper around selected SVG nodes."""

    nodes: list[etree._Element]

    def __iter__(self) -> Iterable[etree._Element]:
        return iter(self.nodes)

    def __len__(self) -> int:
        return len(self.nodes)

    def delete(self) -> Selection:
        for node in list(self.nodes):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
        self.nodes.clear()
        return self

    def set_attr(self, name: str, value: str | int | float) -> Selection:
        attr = name.replace("_", "-")
        for node in self.nodes:
            node.set(attr, str(value))
        return self

    def set_style(self, **style: str | int | float) -> Selection:
        """Set inline CSS on each node, and wherever a descendant declares it too.

        Placed content often styles its leaves directly -- Matplotlib a line's
        path, VecWire a symbol's strokes -- and a leaf's own declaration wins
        over anything it would inherit.  So a descendant that declares one of
        these properties, inline or as a presentation attribute, has it
        replaced.  A declared ``none`` is kept: recolouring a line must not
        fill it.
        """
        values = {key.replace("_", "-"): str(value) for key, value in style.items()}
        for node in self.nodes:
            current = _style_to_dict(node.get("style"))
            node.set("style", _dict_to_style(current | values))
            for child in node.iterdescendants(etree.Element):
                declared = _style_to_dict(child.get("style"))
                for key, value in values.items():
                    if key in declared:
                        if declared[key] != "none":
                            declared[key] = value
                    elif child.get(key) not in (None, "none"):
                        child.set(key, value)
                if declared:
                    child.set("style", _dict_to_style(declared))
        return self


def select(root: etree._Element, selector: str) -> Selection:
    """Select by #id, .class, or tag name."""

    if not selector:
        raise ValueError("Selector cannot be empty")

    if selector.startswith("#"):
        wanted = selector[1:]
        if not wanted:
            raise ValueError("ID selector cannot be empty")
        nodes = [node for node in root.iter() if node.get("id") == wanted]
        return Selection(nodes)

    if selector.startswith("."):
        wanted = selector[1:]
        if not wanted:
            raise ValueError("Class selector cannot be empty")
        nodes = [node for node in root.iter() if wanted in (node.get("class") or "").split()]
        return Selection(nodes)

    if any(char.isspace() for char in selector):
        raise ValueError(f"Unsupported selector: {selector!r}")

    nodes = [node for node in root.iter() if local_name(node) == selector]
    return Selection(nodes)
