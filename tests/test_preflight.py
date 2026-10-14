"""Preflight reports observable risks without rendering or changing the figure."""

import base64
from io import BytesIO

import pytest
from lxml import etree
from PIL import Image

from figworks import Figure
from figworks.fonts import ResolvedFace


def fonts(face):
    return ResolvedFace("/fake/font.otf", (face.family,), ((0, 0x10FFFF),))


def figure(body, width=200, height=100):
    fig = Figure(width, height)
    wrapper = etree.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>')
    fig.document.root.extend(wrapper)
    return fig


def codes(report):
    return [item.code for item in report.issues]


def test_report_is_read_only_repeatable_and_does_not_replace_export_policy():
    fig = figure('<rect id="box" x="10" y="10" width="20" height="20"/>', "100mm", "50mm")
    before = fig.document.to_string()
    report = fig.check(resolve_fonts=fonts)
    assert report.ok
    assert not report.issues
    assert not report.unchecked
    assert report == fig.check(resolve_fonts=fonts)
    assert fig.document.to_string() == before
    report.raise_for_errors()


def test_duplicate_ids_and_missing_references_are_errors():
    fig = figure('<g id="same"/><g id="same"/><use href="#missing"/>')
    report = fig.check(resolve_fonts=fonts)
    assert not report.ok
    assert codes(report) == ["duplicate-id", "broken-reference"]
    assert report.issues[0].element_id == "same"
    assert report.issues[0].path
    with pytest.raises(ValueError, match="missing"):
        report.raise_for_errors()


def test_font_failures_are_collected():
    fig = figure('<text font-family="Missing">Hello</text>')
    report = fig.check(resolve_fonts=lambda face: None)
    assert not report.ok
    assert "font" in codes(report)
    assert "Missing" in report.issues[0].message


def test_import_scaling_changes_text_and_stroke_thresholds():
    fig = Figure(100, 100)
    fig.panel("p", 0, 0, 50, 50).add(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<text id="label" font-size="8pt">Hello</text>'
        '<line id="curve" x1="10" y1="10" x2="90" y2="10" stroke="black" '
        'stroke-width="0.3pt"/></svg>',
        id="plot",
    )
    report = fig.check(resolve_fonts=fonts)
    assert {"small-text", "thin-stroke"} <= set(codes(report))
    assert report.ok  # thresholds are warnings, not structural errors
    assert any("4 pt" in item.message for item in report.issues)
    assert any("0.15 pt" in item.message for item in report.issues)
    disabled = fig.check(min_font_pt=0, min_stroke_pt=0, resolve_fonts=fonts)
    assert "small-text" not in codes(disabled)
    assert "thin-stroke" not in codes(disabled)


def test_inline_overrides_inheritance_and_nonuniform_transform():
    fig = figure(
        '<g font-size="20pt" transform="rotate(30) scale(0.2 3)">'
        '<text id="small" style="font-size: 8pt">Hi</text></g>'
    )
    report = fig.check(resolve_fonts=fonts)
    issue = next(item for item in report.issues if item.code == "small-text")
    assert issue.element_id == "small"
    assert "1.6 pt" in issue.message


def test_page_bounds_follow_transform_order():
    inside = figure(
        '<g transform="translate(100 0) scale(2)"><rect x="10" y="10" width="20" height="20"/></g>'
    )
    outside = figure(
        '<g transform="scale(2) translate(100 0)"><rect x="10" y="10" width="20" height="20"/></g>'
    )
    assert "outside-page" not in codes(inside.check(resolve_fonts=fonts))
    assert "outside-page" in codes(outside.check(resolve_fonts=fonts))


def test_clipping_complex_geometry_and_css_are_explicitly_unchecked():
    fig = figure(
        '<defs><clipPath id="clip"><rect width="10" height="10"/></clipPath></defs>'
        '<g clip-path="url(#clip)"><rect width="500" height="500"/></g>'
        '<path d="M0 0 C100 500 200 100 0 0"/>'
    )
    report = fig.check(resolve_fonts=fonts)
    assert "outside-page" not in codes(report)
    assert any("bounds" in item for item in report.unchecked)
    styled = figure("<style>text {font-size: 20pt; font-family: Custom}</style><text>hi</text>")
    report = styled.check(resolve_fonts=lambda face: pytest.fail("CSS font selection is unknown"))
    assert report.ok
    assert any("Stylesheets" in item for item in report.unchecked)


def test_hidden_shapes_and_definitions_are_not_measured():
    fig = figure(
        '<defs><rect width="999" height="999"/></defs>'
        '<g display="none"><rect width="999" height="999"/></g>'
    )
    assert not fig.check(resolve_fonts=fonts).issues


def raster(width=100, height=100):
    buffer = BytesIO()
    Image.new("RGB", (width, height)).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def test_raster_dpi_uses_physical_placement_and_aspect_ratio():
    # 100 pixels at 96 CSS px (one inch) is 100 dpi.
    fig = figure(f'<image href="{raster()}" width="96" height="96"/>')
    report = fig.check(resolve_fonts=fonts)
    assert {"embedded-image", "low-resolution"} <= set(codes(report))
    assert "100 dpi" in next(
        item.message for item in report.issues if item.code == "low-resolution"
    )
    # Meet scales the image to 24 px, not the wider viewport.
    fig = figure(f'<image href="{raster()}" width="96" height="24"/>')
    assert "low-resolution" not in codes(fig.check(resolve_fonts=fonts))
    fig = figure(f'<image href="{raster()}" width="96" height="24" preserveAspectRatio="none"/>')
    assert "low-resolution" in codes(fig.check(resolve_fonts=fonts))
    fig = figure(f'<g transform="scale(4)"><image href="{raster()}" width="24" height="24"/></g>')
    assert "low-resolution" in codes(fig.check(resolve_fonts=fonts))


def test_external_resources_are_reported_without_fetching():
    fig = figure(
        '<image href="https://invalid.example/chart.png" width="40" height="40"/>'
        '<rect width="5" height="5" fill="url(other.svg#gradient)"/>'
    )
    report = fig.check(resolve_fonts=fonts)
    assert codes(report).count("external-resource") == 2
    assert any("external" in item for item in report.unchecked)


def test_bad_image_does_not_abort_report():
    fig = figure('<image href="data:image/png;base64,broken" width="40" height="40"/>')
    assert "image-unreadable" in codes(fig.check(resolve_fonts=fonts))


def test_export_feature_warning_depends_on_target():
    fig = figure('<foreignObject/><filter id="f"/><animate attributeName="x"/>')
    assert codes(fig.check(resolve_fonts=fonts)).count("export-feature") == 3
    assert "export-feature" not in codes(fig.check(target="svg", resolve_fonts=fonts))


@pytest.mark.parametrize("transform", ["translate(10px)", "bogus(1)", "scale(1 2 3)"])
def test_unknown_transform_is_not_silently_ignored(transform):
    fig = figure(f'<g transform="{transform}"><rect width="500" height="500"/></g>')
    report = fig.check(resolve_fonts=fonts)
    assert any("transforms" in item for item in report.unchecked)
    assert "outside-page" not in codes(report)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_thresholds(value):
    with pytest.raises(ValueError, match="threshold"):
        Figure(100, 100).check(min_font_pt=value)


def test_unknown_target():
    with pytest.raises(ValueError, match="target"):
        Figure(100, 100).check(target="eps")


def test_hidden_and_unused_text_do_not_require_fonts():
    fig = figure(
        '<defs><text font-family="Missing">Unused</text></defs>'
        '<g display="none"><text font-family="Missing">Hidden</text></g>'
        '<text visibility="hidden" font-family="Missing">Hidden</text>'
    )
    report = fig.check(resolve_fonts=lambda face: pytest.fail("unused text must not resolve fonts"))
    assert report.ok


def test_visible_child_of_hidden_text_is_checked():
    fig = figure(
        '<text visibility="hidden" font-family="Missing">Hidden'
        '<tspan visibility="visible">Visible</tspan></text>'
    )
    assert not fig.check(resolve_fonts=lambda face: None).ok


def test_nested_viewport_measurements_are_unchecked():
    fig = figure(
        '<svg viewBox="0 0 10 10" width="100" height="100">'
        '<text font-size="1">Not one output pixel</text></svg>'
    )
    report = fig.check(resolve_fonts=fonts)
    assert "small-text" not in codes(report)
    assert any("viewports" in item for item in report.unchecked)


def test_matplotlib_caps_stylesheet_does_not_disable_font_measurements():
    fig = figure(
        "<defs><style>*{stroke-linejoin: round; stroke-linecap: butt}</style></defs>"
        '<text font-size="3pt">Small</text>'
    )
    report = fig.check(resolve_fonts=fonts)
    assert "small-text" in codes(report)
    assert not any("Stylesheets" in item for item in report.unchecked)


def test_page_sized_native_background_tolerates_svg_number_rounding():
    fig = Figure("180mm", "130mm")
    fig.rect(x=0, y=0, width="180mm", height="130mm", fill="white", stroke="none")
    assert "outside-page" not in codes(fig.check(resolve_fonts=fonts))


def test_uniform_point_viewport_uses_physical_sizes():
    fig = Figure(200, 100)
    fig.document.root.set("width", "200pt")
    fig.document.root.set("height", "100pt")
    fig.document.root.append(etree.fromstring('<text id="label" font-size="8">Eight points</text>'))
    report = fig.check(resolve_fonts=fonts, min_font_pt=7)
    assert "viewport" not in codes(report)
    assert "small-text" not in codes(report)


def test_findings_name_nearest_semantic_group_but_keep_exact_path():
    fig = figure('<g id="spectrum"><text font-size="2">Tiny</text></g>')
    issue = next(
        item for item in fig.check(resolve_fonts=fonts).issues if item.code == "small-text"
    )
    assert issue.element_id == "spectrum"
    assert issue.path.endswith("/*") or "text" in issue.path
