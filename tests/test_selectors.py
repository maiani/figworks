from figworks.core.document import SVGDocument


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


def test_set_style_reaches_a_matplotlib_line_by_its_gid():
    import matplotlib.pyplot as plt

    from figworks import Figure

    mpl_fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    line.set_gid("curve")
    fig = Figure("60mm", "40mm")
    fig.panel("p", 0, 0, "60mm", "40mm").add(mpl_fig, id="plot")
    plt.close(mpl_fig)

    fig.select("#curve").set_style(stroke="#c2185b", fill="#c2185b")
    (path,) = fig.select("#curve").nodes[0].iter("{http://www.w3.org/2000/svg}path")
    assert "stroke: #c2185b" in path.get("style")
    assert "fill: none" in path.get("style")  # a line stays unfilled


def test_set_style_replaces_presentation_attributes_but_keeps_none():
    document = SVGDocument("100px", "100px")
    symbol = document.append(document.element("g", id="JJ"))
    document.append(document.element("path", stroke="#262626", fill="none"), parent=symbol)
    document.append(document.element("circle", r=1, fill="#262626"), parent=symbol)

    document.select("#JJ").set_style(stroke="red", fill="red")
    path, circle = symbol
    assert (path.get("stroke"), path.get("fill")) == ("red", "none")
    assert (circle.get("stroke"), circle.get("fill")) == (None, "red")
    assert symbol.get("style") == "stroke: red; fill: red"
