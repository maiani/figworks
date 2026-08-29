from figforge.core.document import SVGDocument


def test_id_class_and_tag_selection():
    document = SVGDocument("100px", "100px")
    document.append(document.element("text", "A", id="title", class_="label"))
    document.append(document.element("rect", id="box", class_="shape important"))

    assert len(document.select("#title")) == 1
    assert len(document.select(".shape")) == 1
    assert len(document.select("text")) == 1


def test_delete_and_set_style():
    document = SVGDocument("100px", "100px")
    document.append(document.element("text", "A", id="title", class_="label"))
    document.append(document.element("rect", id="box"))

    document.select("#title").set_style(font_size="8pt", fill="red")
    assert "font-size: 8pt" in document.to_string()
    assert "fill: red" in document.to_string()

    document.select("#box").delete()
    assert 'id="box"' not in document.to_string()
