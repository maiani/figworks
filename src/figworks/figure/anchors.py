"""Anchor points for figures and panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Anchor:
    """A named absolute point in SVG pixel coordinates."""

    x: float
    y: float
    name: str | None = None

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
