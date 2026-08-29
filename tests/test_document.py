from figforge.core.document import SVGDocument
from figforge.core.element import SVG_NS


def test_document_creation_and_group():
    document = SVGDocument("100mm", "50mm")
    document.group(id="panel", class_="figforge-panel")
    output = document.to_string()

    assert 'width="100mm"' in output
    assert 'height="50mm"' in output
    assert 'id="panel"' in output
    assert all(
        not isinstance(node.tag, str) or node.tag.startswith(f"{{{SVG_NS}}}")
        for node in document.root.iter()
    )


def test_import_svg_group():
    document = SVGDocument("100px", "100px")
    document.import_svg(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="x">Hi</text></svg>', id="imported"
    )

    output = document.to_string()
    assert 'id="imported"' in output
    assert 'id="x"' in output
