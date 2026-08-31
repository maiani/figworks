import matplotlib.pyplot as plt

from figforge import Figure, layout_svgs
from figforge.matplotlib import mpl_to_svg


def _svg(label="content"):
    mpl_fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1], [0, 1])
    ax.set_title(label)
    return mpl_to_svg(mpl_fig)


def test_placeholder_and_fill_native():
    fig = Figure(width="200px", height="100px")
    fig.placeholder("slot", x=10, y=10, w=80, h=70, label="reserved")

    out = fig.document.to_string()
    assert 'id="slot"' in out
    assert 'class="figforge-placeholder"' in out

    fig.document.fill("slot", _svg("native"))
    out = fig.document.to_string()
    assert "native" in out
    assert 'class="figforge-placeholder"' not in out
    assert "reserved" not in out


def test_fill_raises_for_missing_id():
    fig = Figure(width="100px", height="100px")
    try:
        fig.document.fill("missing", _svg())
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for missing id")


def test_figure_fill_accepts_mpl_figure():
    fig = Figure(width="200px", height="100px")
    fig.placeholder("p", x=0, y=0, w=100, h=80)

    mpl_fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_title("mpl-source")

    fig.fill("p", mpl_fig)
    assert "mpl-source" in fig.document.to_string()


def test_figure_fill_accepts_svg_file(tmp_path):
    svg_file = tmp_path / "panel.svg"
    svg_file.write_text(_svg("file-source"), encoding="utf-8")

    fig = Figure(width="200px", height="100px")
    fig.placeholder("p", x=0, y=0, w=100, h=80)
    fig.fill("p", svg_file)
    assert "file-source" in fig.document.to_string()


def test_layout_svgs_grid_with_labels_and_outlines():
    fig = layout_svgs(
        [_svg("A"), _svg("B"), _svg("C"), _svg("D")],
        labels=["a", "b", "c", "d"],
        outline=True,
        shape=(2, 2),
    )
    out = fig.document.to_string()
    for label in ("A", "B", "C", "D"):
        assert label in out
    assert out.count("figforge-cell-label") == 4
    assert out.count("figforge-cell-outline") == 4
