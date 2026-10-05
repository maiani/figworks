import matplotlib.pyplot as plt

from figforge import Figure
from figforge.matplotlib import mpl_to_svg


def test_matplotlib_export_contains_gid_and_text():
    mpl_fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    line.set_gid("semantic-line")
    ax.set_xlabel("x axis")

    svg = mpl_to_svg(mpl_fig)

    assert "semantic-line" in svg
    assert "x axis" in svg


def test_matplotlib_export_is_byte_identical():
    """Clip-path ids are salted and the date stamped unless FigForge pins both."""

    def export():
        mpl_fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], marker="o")
        svg = mpl_to_svg(mpl_fig)
        plt.close(mpl_fig)
        return svg

    first = export()
    assert "clipPath" in first, "the export must contain the salted ids this guards"
    assert first == export()
    assert "<dc:date>" not in first


def test_matplotlib_export_restores_rcparams():
    before = {key: plt.rcParams[key] for key in ("svg.fonttype", "svg.hashsalt")}
    mpl_fig, _ = plt.subplots()
    mpl_to_svg(mpl_fig)
    plt.close(mpl_fig)
    assert {key: plt.rcParams[key] for key in before} == before


def test_panel_imports_matplotlib_svg():
    mpl_fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    fig = Figure(width="100mm", height="60mm")
    panel = fig.panel("main", x="5mm", y="5mm", w="50mm", h="30mm")
    panel.add(mpl_fig, id="mpl-panel")

    output = fig.document.to_string()
    assert 'id="mpl-panel"' in output


def test_panel_accepts_a_generic_svg_document_provider():
    class Provider:
        def to_svg_document(self):
            return (
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'viewBox="0 0 100 100"><rect id="plot"/></svg>'
            )

    fig = Figure(width="200px", height="100px")
    panel = fig.panel("main", x=0, y=0, w=200, h=100)
    node = panel.add(Provider(), id="square-plot")

    assert node.get("transform") == "translate(50 0) scale(1)"
