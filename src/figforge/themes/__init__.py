"""Small built-in style presets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    font_family: str = "Arial"
    base_font_size: str = "8pt"
    stroke_width: str = "1pt"
    stroke: str = "black"
    panel_label_font_size: str = "10pt"


paper = Theme()
presentation = Theme(
    base_font_size="11pt",
    stroke_width="1.3pt",
    panel_label_font_size="14pt",
)

THEMES = {
    "paper": paper,
    "presentation": presentation,
}


def get_theme(theme: str | Theme) -> Theme:
    if isinstance(theme, Theme):
        return theme
    try:
        return THEMES[theme]
    except KeyError as exc:
        raise ValueError(f"Unknown theme: {theme!r}") from exc


__all__ = ["THEMES", "Theme", "get_theme", "paper", "presentation"]
