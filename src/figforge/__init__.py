"""Public FigForge API."""

from figforge.collection import FigureCollection
from figforge.core.display import display_svg
from figforge.figure import Anchor, Figure, Panel, Theme
from figforge.figure.layout import layout_svgs
from figforge.matplotlib import compose

__all__ = [
    "Anchor",
    "Figure",
    "FigureCollection",
    "Panel",
    "Theme",
    "__version__",
    "compose",
    "display_svg",
    "layout_svgs",
]

__version__ = "0.1.0"
