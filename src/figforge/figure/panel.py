"""Panel model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from figforge.core.units import to_px
from figforge.figure.anchors import Anchor

if TYPE_CHECKING:
    from figforge.figure.figure import Figure


@dataclass
class Panel:
    """Rectangular figure region with local content."""

    figure: Figure
    id: str
    x: float
    y: float
    w: float
    h: float

    @property
    def nw(self) -> Anchor:
        return Anchor(self.x, self.y, f"{self.id}.nw")

    @property
    def ne(self) -> Anchor:
        return Anchor(self.x + self.w, self.y, f"{self.id}.ne")

    @property
    def sw(self) -> Anchor:
        return Anchor(self.x, self.y + self.h, f"{self.id}.sw")

    @property
    def se(self) -> Anchor:
        return Anchor(self.x + self.w, self.y + self.h, f"{self.id}.se")

    @property
    def center(self) -> Anchor:
        return Anchor(self.x + self.w / 2, self.y + self.h / 2, f"{self.id}.center")

    @property
    def north(self) -> Anchor:
        return Anchor(self.x + self.w / 2, self.y, f"{self.id}.north")

    @property
    def south(self) -> Anchor:
        return Anchor(self.x + self.w / 2, self.y + self.h, f"{self.id}.south")

    @property
    def east(self) -> Anchor:
        return Anchor(self.x + self.w, self.y + self.h / 2, f"{self.id}.east")

    @property
    def west(self) -> Anchor:
        return Anchor(self.x, self.y + self.h / 2, f"{self.id}.west")

    def anchor(self, name: str) -> Anchor:
        try:
            value = getattr(self, name)
        except AttributeError as exc:
            raise ValueError(f"Unknown panel anchor: {name!r}") from exc
        if not isinstance(value, Anchor):
            raise ValueError(f"Unknown panel anchor: {name!r}")
        return value

    def add(self, source, id: str | None = None, *, preserve_aspect_ratio: bool = True):
        """Place an SVG document provider, Matplotlib figure, or SVG source."""
        return self.figure.add(
            source,
            x=self.x,
            y=self.y,
            w=self.w,
            h=self.h,
            id=id,
            preserve_aspect_ratio=preserve_aspect_ratio,
        )

    def text(
        self,
        text: str,
        x: str | int | float,
        y: str | int | float,
        id: str | None = None,
        **attrs,
    ):
        return self.figure.text(text, self.x + to_px(x), self.y + to_px(y), id=id, **attrs)
