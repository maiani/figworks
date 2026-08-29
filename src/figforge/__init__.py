"""Public FigForge API."""

from figforge._version import __version__
from figforge.core.display import display_svg
from figforge.figure import Anchor, Figure, Panel
from figforge.figure.layout import layout_svgs
from figforge.themes import Theme

__all__ = [
    "Anchor",
    "Figure",
    "Panel",
    "Theme",
    "__version__",
    "display_svg",
    "layout_svgs",
]
