"""Source semantics and atomic failures at the SVG import boundary."""

import pytest
from lxml import etree
from PIL import Image

from figworks import Figure
from figworks.core.element import _references
from figworks.matplotlib import insert


def source(body, attrs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" {attrs}>{body}</svg>'


def test_root_identity_style_and_transform_survive_placement(tmp_path):
    fig = Figure(20, 20)
    fig.add(
        source(
            '<rect width="5" height="10"/>',
            'id="source" class="original" fill="red" opacity="0.5" transform="translate(2 0)"',
        ),
        x=0,
        y=0,
        w=20,
        h=20,
        id="placed",
    )
    (root,) = fig.select("#source")
    assert root.get("class") == "original"
    assert root.get("transform") == "translate(2 0)"
    png = tmp_path / "root.png"
    fig.save(png, dpi=96)
    with Image.open(png) as image:
        rgba = image.convert("RGBA")
        assert rgba.getpixel((1, 5))[3] == 0
        assert rgba.getpixel((6, 5)) == (255, 0, 0, 128)


def test_definition_inheritance_stays_with_its_source(tmp_path):
    body = (
        '<defs><linearGradient id="paint"><stop stop-color="currentColor"/>'
        '<stop offset="1" stop-color="currentColor"/></linearGradient></defs>'
        '<rect width="10" height="10" fill="url(#paint)"/>'
    )
    fig = Figure(20, 10)
    fig.add(source(body, 'color="red"'), x=0, y=0, w=10, h=10, id="left")
    fig.add(source(body, 'color="blue"'), x=10, y=0, w=10, h=10, id="right")
    png = tmp_path / "colors.png"
    fig.save(png, dpi=96)
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        assert rgb.getpixel((5, 5)) == (255, 0, 0)
        assert rgb.getpixel((15, 5)) == (0, 0, 255)


def test_comments_processing_instructions_and_text_spaces_survive_import():
    fig = Figure(20, 10)
    fig.add(
        source("<!--note--><?editor kept?><text><tspan>A</tspan> <tspan>B</tspan></text>"),
        x=0,
        y=0,
        w=10,
        h=10,
    )
    assert len(fig.select("text")) == 1
    (text,) = fig.select("text")
    assert text[0].tail == " "
    assert "<!--note-->" in fig.document.to_string()
    assert fig.check().ok


def test_nested_placement_keeps_its_inherited_definition_color(tmp_path):
    drawing = source(
        '<defs><linearGradient id="paint"><stop stop-color="currentColor"/>'
        '</linearGradient></defs><rect width="10" height="10" fill="url(#paint)"/>'
    )
    fig = Figure(20, 10)
    fig.add(drawing, x=0, y=0, w=10, h=10)
    parent = fig.document.group(transform="translate(10 0)")
    parent.set("color", "red")
    fig.document.place(drawing, 0, 0, 10, 10, parent=parent)
    png = tmp_path / "nested.png"
    fig.save(png, dpi=96)
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        assert rgb.getpixel((5, 5)) == (0, 0, 0)
        assert rgb.getpixel((15, 5)) == (255, 0, 0)


@pytest.mark.parametrize(
    "invalid",
    [
        "<svg><g></svg>",
        '<svg viewBox="0 0 nan 10"/>',
        '<svg viewBox="0 0 -1 10"/>',
        '<svg viewBox="0 0 0 10"/>',
        "<html/>",
        source('<rect id="same"/><circle id="same"/>'),
        source('<rect id=""/>'),
    ],
)
def test_failed_add_and_fill_leave_the_document_unchanged(invalid):
    fig = Figure(20, 10)
    fig.placeholder("slot", 0, 0, 10, 10, label="reserved")
    before = fig.document.to_string()
    with pytest.raises((ValueError, etree.XMLSyntaxError)):
        fig.add(invalid, x=0, y=0, w=10, h=10, id="bad")
    assert fig.document.to_string() == before
    with pytest.raises((ValueError, etree.XMLSyntaxError)):
        fig.fill("slot", invalid)
    assert fig.document.to_string() == before


def test_nested_definition_ids_remain_valid_when_the_definition_is_shared():
    drawing = source(
        '<defs><g id="shape"><path id="part" d="M0 0h10v10H0z"/></g></defs>'
        '<use href="#shape"/><use href="#part"/>'
    )
    fig = Figure(20, 10)
    for index in range(2):
        fig.add(drawing, x=10 * index, y=0, w=10, h=10, id=f"p{index}")
    assert len(fig.select("#shape")) == len(fig.select("#part")) == 1
    ids = set(fig.document.root.xpath("//@id"))
    assert _references(fig.document.root) <= ids


def test_nested_shared_definition_is_copied_when_its_dependency_changes():
    def drawing(color):
        return source(
            f'<defs><linearGradient id="paint"><stop stop-color="{color}"/></linearGradient>'
            '<g id="shape"><path id="part" fill="url(#paint)" d="M0 0h10v10H0z"/></g>'
            '</defs><use href="#part"/>'
        )

    fig = Figure(20, 10)
    fig.add(drawing("red"), x=0, y=0, w=10, h=10, id="left")
    fig.add(drawing("blue"), x=10, y=0, w=10, h=10, id="right")
    assert len(fig.select("#right-part")) == 1
    assert next(iter(fig.select("#right-part"))).get("fill") == "url(#right-paint)"
    assert _references(fig.document.root) <= set(fig.document.root.xpath("//@id"))


def test_root_id_does_not_collide_with_the_placement_id():
    fig = Figure(10, 10)
    fig.add(source('<rect width="10" height="10"/>', 'id="same"'), x=0, y=0, w=10, h=10, id="same")
    assert len(fig.select("#same")) == len(fig.select("#same-same")) == 1


def test_replacement_does_not_share_definitions_with_the_removed_subtree():
    drawing = source(
        '<!--definition--><defs><linearGradient id="paint"><stop stop-color="red"/>'
        '</linearGradient></defs><rect width="10" height="10" fill="url(#paint)"/>'
    )
    fig = Figure(10, 10)
    fig.add(drawing, x=0, y=0, w=10, h=10, id="slot")
    fig.fill("slot", drawing)
    assert len(fig.select("#paint")) == 1
    assert _references(fig.document.root) <= set(fig.document.root.xpath("//@id"))


def test_matplotlib_replacement_keeps_source_root_attributes():
    destination = source('<rect id="slot" width="10" height="10"/>')
    result = insert(
        {"slot": source('<rect width="10" height="10"/>', 'fill="red" id="source"')},
        svg=destination,
    )
    root = etree.fromstring(result.encode())
    assert root.xpath("//*[@id='source']/@fill") == ["red"]
