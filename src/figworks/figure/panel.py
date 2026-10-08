"""Panel model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from figworks.core.units import to_px
from figworks.figure.anchors import Anchor

if TYPE_CHECKING:
    from lxml import etree
    from matplotlib.figure import Figure as MplFigure

    from figworks.figure.figure import Figure


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

    def add(
        self,
        source: Any,
        id: str | None = None,
        *,
        preserve_aspect_ratio: bool = True,
        fit: Literal["content", "axes", "none"] = "content",
        align: str = "center",
    ) -> etree._Element:
        """Place an SVG document provider, Matplotlib figure, or SVG source.

        See :meth:`Figure.add` for ``fit`` and ``align``; ``fit="none"`` keeps
        the source's own physical size.
        """
        return self.figure.add(
            source,
            x=self.x,
            y=self.y,
            w=self.w,
            h=self.h,
            id=id,
            preserve_aspect_ratio=preserve_aspect_ratio,
            fit=fit,
            align=align,
        )

    def subplots(self, nrows: int = 1, ncols: int = 1, **kwargs: Any) -> tuple[MplFigure, Any]:
        """A Matplotlib figure whose axes frame is exactly this panel.

        The figure has the panel's physical size and its axes grid fills it
        edge to edge; tick and axis labels fall outside, into the space around
        the panel.  Place it with ``fit="axes"`` and it lands at 1:1, so text
        keeps its nominal size and the frame sits exactly on the panel::

            mpl_fig, ax = panel.subplots()
            ax.plot(x, y)
            panel.add(mpl_fig, id="spectrum", fit="axes")

        Leave room for the labels when laying out panels.  Arguments are those
        of :func:`matplotlib.pyplot.subplots`; ``gridspec_kw`` may set
        ``wspace`` and ``hspace`` between axes, but not the outer edges, and no
        layout engine is used, since it would move the frame.
        """
        import matplotlib.pyplot as plt

        if "figsize" in kwargs or "layout" in kwargs:
            raise ValueError("the panel sets the figure size and layout")
        gridspec = dict(kwargs.pop("gridspec_kw", None) or {})
        if {"left", "right", "bottom", "top"} & gridspec.keys():
            raise ValueError("the panel sets the axes grid's outer edges")
        gridspec.update(left=0.0, right=1.0, bottom=0.0, top=1.0)
        return plt.subplots(
            nrows,
            ncols,
            figsize=(self.w / 96, self.h / 96),
            layout="none",
            gridspec_kw=gridspec,
            **kwargs,
        )

    def text(
        self,
        text: str,
        x: str | int | float,
        y: str | int | float,
        id: str | None = None,
        **attrs: Any,
    ) -> etree._Element:
        return self.figure.text(text, self.x + to_px(x), self.y + to_px(y), id=id, **attrs)
