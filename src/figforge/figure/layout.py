"""Helpers for laying out multiple SVG panels in a grid."""

from __future__ import annotations

import math
from collections.abc import Sequence

from figforge.figure.figure import Figure


def layout_svgs(
    svgs: Sequence[str],
    labels: Sequence[str | None] | None = None,
    outline: bool | Sequence[bool] | None = None,
    shape: tuple[int, int] | None = None,
    cell: tuple[float, float] = (200.0, 140.0),
    gap: float = 20.0,
    fontsize: str = "10pt",
) -> Figure:
    """Assemble multiple SVG strings into a single grid figure.

    Each SVG is given equal space in a grid, with optional per-cell labels and
    outlines. The result is a :class:`figforge.Figure` whose cells are native
    SVG imports.

    :param svgs: list of SVG strings (or sources accepted by :func:`fill`).
    :param labels: optional labels drawn above each cell.
    :param outline: ``True`` to outline all cells, ``False`` for none, or a
        per-cell list of booleans.
    :param shape: optional ``(nrows, ncols)``; inferred from the count otherwise.
    :param cell: ``(width, height)`` of each cell in points.
    :param gap: spacing between cells in points.
    :param fontsize: label font size.
    :returns: a populated :class:`figforge.Figure`.
    """
    from figforge.core.units import to_px

    count = len(svgs)
    if count == 0:
        raise ValueError("At least one SVG is required")

    if labels is None:
        labels = [None] * count
    if len(labels) != count:
        raise ValueError("labels must have the same length as svgs")

    nrows, ncols = _grid_shape(count, shape)
    cell_w = to_px(f"{cell[0]}pt")
    cell_h = to_px(f"{cell[1]}pt")
    gap_px = to_px(f"{gap}pt")
    label_gap = to_px("14pt")

    has_label = any(label is not None for label in labels)
    width_total = ncols * cell_w + (ncols - 1) * gap_px
    height_total = nrows * cell_h + (nrows - 1) * gap_px
    if has_label:
        height_total += label_gap

    fig = Figure(width=f"{width_total}px", height=f"{height_total}px")

    outlines = _outline_list(outline, count)
    for index, (svg, label, draw_outline) in enumerate(zip(svgs, labels, outlines, strict=True)):
        row, col = divmod(index, ncols)
        cell_x = col * (cell_w + gap_px)
        cell_y = row * (cell_h + gap_px) + (label_gap if has_label else 0)
        pid = f"cell-{index}"
        if draw_outline:
            fig.rect(
                x=cell_x,
                y=cell_y,
                width=cell_w,
                height=cell_h,
                class_="figforge-cell-outline",
                fill="none",
                stroke="black",
            )
        if label is not None:
            fig.text(
                label,
                x=cell_x + cell_w / 2,
                y=cell_y - 3,
                class_="figforge-cell-label",
                text_anchor="middle",
                font_size=fontsize,
            )
        fig.add(svg, x=cell_x, y=cell_y, w=cell_w, h=cell_h, id=pid)

    return fig


def _grid_shape(count: int, shape: tuple[int, int] | None) -> tuple[int, int]:
    if shape is not None:
        nrows, ncols = shape
        if nrows * ncols != count:
            raise ValueError("shape must contain exactly len(svgs) cells")
        return nrows, ncols
    nrows = math.ceil(math.sqrt(count))
    ncols = math.ceil(count / nrows)
    return nrows, ncols


def _outline_list(outline: bool | Sequence[bool] | None, count: int) -> list[bool]:
    if outline is None:
        return [False] * count
    if isinstance(outline, bool):
        return [outline] * count
    if len(outline) != count:
        raise ValueError("outline must be a bool or have the same length as svgs")
    return list(outline)
