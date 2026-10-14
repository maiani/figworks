# Publication preflight

Check the **assembled figure**, after placement has scaled its text, strokes,
and images:

```python
report = figure.check(target="pdf", min_font_pt=6, min_stroke_pt=0.25, min_raster_dpi=300)
for issue in report.issues:
    print(issue.severity, issue.code, issue.element_id or issue.path, issue.message)
for limitation in report.unchecked:
    print("Not checked:", limitation)
report.raise_for_errors()
figure.save("figure.pdf")
```

`Figure.check()` is explicit and read-only. It does not export, fetch external
resources, repair the document, or change `save()` behavior. It reads embedded
raster headers and uses the existing local fontconfig resolver. Export retains
its existing font check.

## Report and policy

`CheckReport` and `CheckIssue` are exported from `figworks`. Reports hold tuples;
findings have `severity`, `code`, `message`, `element_id`, and an XPath `path`.
IDs identify authored objects where available; XPath identifies other nodes.
Whole-document findings, such as missing reference targets, point at the root.

- **Errors:** duplicate IDs, broken local references, and font/glyph failures.
- **Warnings:** publication thresholds, external resources, potentially
  incompatible export features, unreadable embedded images, and page overflow.
- **Information:** image elements that may contain raster content.

`report.ok` means **no reported errors**. Warnings and unchecked areas may
still exist. `raise_for_errors()` raises `ValueError` only for errors. Choose
any stricter project policy explicitly, for example failing on selected codes:

```python
blocking = {"small-text", "low-resolution"}
if any(issue.code in blocking for issue in report.issues):
    raise ValueError("Figure needs larger labels or higher-resolution images")
```

The defaults—6 pt text, 0.25 pt strokes, and 300 dpi raster images—are adjustable
heuristics, not journal requirements. A zero threshold disables that warning.
Negative or nonfinite thresholds are rejected. Targets are `svg`, `pdf`, and
`png`; the default is `pdf`.

## Checks

| Code | What it reports |
| --- | --- |
| `duplicate-id` | Repeated IDs anywhere in the SVG |
| `broken-reference` | Missing targets for local href and `url(#...)` references |
| `font` | Missing/substituted font, generic family, missing glyph, or unavailable font checker |
| `small-text` | Smallest transformed font size below the threshold |
| `small-script` | A note, not a warning: a sub- or superscript at 0.7 of a label that meets the threshold, as Matplotlib's mathtext and TeX set them |
| `thin-stroke` | Smallest nonzero transformed stroke width below the threshold |
| `embedded-image` | Image content may be raster, even in SVG output |
| `low-resolution` | Embedded raster's minimum effective DPI below the threshold |
| `external-resource` | External href or attribute/inline-style URL; never fetched |
| `export-feature` | Filters, foreign objects, or animation needing inspection for PDF/PNG |
| `script` | Script-dependent content that the checker does not evaluate |
| `image-unreadable` | Embedded raster dimensions could not be inspected |
| `outside-page` | Conservative simple-shape/stroke bounds extend beyond the page |
| `viewport` | Root physical dimensions and viewBox do not match the FigWorks pixel canvas |

A 7 pt label has 4.9 pt first-level scripts, and no label size keeps both
within a 5–7 pt range, so such a script is a `small-script` note. A script
smaller than that, such as a script of a script, is still `small-text`.

PDF/PNG feature warnings reflect the limits of
[CairoSVG's SVG support](https://cairosvg.org/svg_support/). A filter warning does
not mean every filter primitive is unsupported. SVG-target checks do not warn
about those static-export differences; animation and foreign layout remain
outside measurement coverage.

## Measurement boundaries

The checker understands physical/px lengths, inherited presentation attributes,
inline longhand styles, and affine `translate`, `scale`, `rotate`, `skewX`,
`skewY`, and `matrix` transforms. For nonuniform transforms, it uses the minimum
stretch for text/strokes and the maximum stretch for raster resolution. These
are conservative worst-direction estimates, not glyph- or tangent-specific
measurements. Plotly may round exported font sizes slightly.

Raster resolution uses intrinsic pixel dimensions, the placed image viewport,
its aspect-ratio policy, and ancestor transforms. It does not decode pixels,
judge image content, or inspect remote images or SVG embedded as an image.

Bounds are checked for rectangles, image viewports, circles, ellipses, and
lines. Rotated curves and stroke margins may produce conservative warnings.
Clipped/masked/filtered objects, path bounds, glyph outlines, text extents,
markers, patterns, and `use` instances need visual inspection. Text rendered as
paths cannot be checked for nominal font size. Referenced content is checked
structurally, but not expanded for physical measurements.

`report.unchecked` records encountered coverage limits. Stylesheets or inline
font shorthand disable font and physical measurements conservatively, except
for universal stroke-cap/join rules such as Matplotlib exports; those do not
change fonts or physical scale and fit within the bounds padding. Nested
SVG viewports, CSS transforms, relative font/geometry lengths, and unsupported
transforms also leave relevant measurements unchecked. This is not a full CSS
engine, SVG validator, or visual-overlap detector. A report with no findings
cannot certify arbitrary SVG rendering.

See `examples/publication_preflight.py` for a deliberately flawed figure and
its structured report.

Uniform physical root viewports (including Matplotlib point units) are measured
in physical units. Findings retain the exact XPath and use the nearest ancestor
ID when the offending node has no ID of its own.
