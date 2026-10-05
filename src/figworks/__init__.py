"""Public FigWorks API."""

from figworks.collection import FigureCollection
from figworks.core.display import display_svg
from figworks.figure import Anchor, Figure, Panel, Theme
from figworks.figure.layout import layout_svgs
from figworks.matplotlib import compose
from figworks.style import load_theme

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
    "load_theme",
]

__version__ = "0.7.0"
