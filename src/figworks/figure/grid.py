"""Rectangle calculations for named panel grids."""

from __future__ import annotations

import math
from collections.abc import Sequence

from figworks.core.units import to_px

type Length = str | int | float
type Margins = Length | tuple[Length, Length, Length, Length]
type Gap = Length | tuple[Length, Length]
type GridLayout = Sequence[Sequence[str | None]]
type Box = tuple[float, float, float, float]


def grid_boxes(
    layout: GridLayout,
    width: float,
    height: float,
    *,
    width_ratios: Sequence[float] | None,
    height_ratios: Sequence[float] | None,
    margins: Margins,
    gap: Gap,
) -> dict[str, Box]:
    """Resolve a rectangular name matrix to boxes in document px."""
    if isinstance(layout, (str, bytes)) or not layout:
        raise ValueError("layout must be a non-empty sequence of rows")
    rows = []
    for row in layout:
        if isinstance(row, (str, bytes)) or not row:
            raise ValueError("each layout row must be a non-empty sequence of panel IDs")
        rows.append(tuple(row))
    nrows, ncols = len(rows), len(rows[0])
    if any(len(row) != ncols for row in rows):
        raise ValueError("layout rows must have the same length")

    cells: dict[str, list[tuple[int, int]]] = {}
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            if name is None:
                continue
            if not isinstance(name, str) or not name.strip():
                raise ValueError("panel IDs must be non-empty strings; use None for empty cells")
            cells.setdefault(name, []).append((r, c))
    if not cells:
        raise ValueError("layout must contain at least one panel")

    spans = {}
    for name, positions in cells.items():
        r0, r1 = min(r for r, _ in positions), max(r for r, _ in positions)
        c0, c1 = min(c for _, c in positions), max(c for _, c in positions)
        if len(positions) != (r1 - r0 + 1) * (c1 - c0 + 1):
            raise ValueError(f"panel {name!r} must occupy one filled rectangle")
        spans[name] = r0, r1, c0, c1

    if isinstance(margins, tuple):
        if len(margins) != 4:
            raise ValueError("margins must be a length or (top, right, bottom, left)")
        top, right, bottom, left = (_length(value, "margins") for value in margins)
    else:
        top = right = bottom = left = _length(margins, "margins")
    if isinstance(gap, tuple):
        if len(gap) != 2:
            raise ValueError("gap must be a length or (row_gap, column_gap)")
        row_gap, column_gap = (_length(value, "gap") for value in gap)
    else:
        row_gap = column_gap = _length(gap, "gap")

    xs, ws = _tracks(width, left, right, column_gap, ncols, width_ratios, "width_ratios")
    ys, hs = _tracks(height, top, bottom, row_gap, nrows, height_ratios, "height_ratios")
    return {
        name: (xs[c0], ys[r0], xs[c1] + ws[c1] - xs[c0], ys[r1] + hs[r1] - ys[r0])
        for name, (r0, r1, c0, c1) in spans.items()
    }


def _length(value: Length, name: str) -> float:
    result = to_px(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must contain finite, non-negative lengths")
    return result


def _tracks(
    extent: float,
    before: float,
    after: float,
    gap: float,
    count: int,
    ratios: Sequence[float] | None,
    name: str,
) -> tuple[list[float], list[float]]:
    if not math.isfinite(extent) or extent <= 0:
        raise ValueError("grid requires finite, positive figure dimensions")
    weights = [1.0] * count if ratios is None else list(ratios)
    if len(weights) != count:
        raise ValueError(f"{name} must have {count} entries")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        for value in weights
    ):
        raise ValueError(f"{name} must contain finite, positive numbers")
    available = extent - before - after - gap * (count - 1)
    if not math.isfinite(available) or available <= 0:
        raise ValueError("margins and gaps leave no room for grid panels")
    # Normalize first so large, otherwise valid ratios cannot overflow their sum.
    largest = max(weights)
    weights = [value / largest for value in weights]
    total = math.fsum(weights)
    sizes = [available * (value / total) for value in weights]
    if any(size <= 0 for size in sizes):
        raise ValueError(f"{name} ratios are too extreme to give every track positive space")
    starts = [before]
    for size in sizes[:-1]:
        starts.append(starts[-1] + size + gap)
    if any(start + size <= start for start, size in zip(starts, sizes, strict=True)):
        raise ValueError(f"{name} ratios are too extreme to give every track positive space")
    return starts, sizes
