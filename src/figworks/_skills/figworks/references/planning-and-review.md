# Planning and reviewing a figure

Use the relevant checks for a new composition, scientific revision, or final
review. Keep a brief in existing project notes or script comments when useful;
small cosmetic edits do not need a separate planning artifact.

## Panel purpose and provenance

For each panel, identify the question it answers, its source file/model, the
variables and units plotted, and the inference it supports. Give added panels
a reason to exist: a control, a different observable, a mechanism, or a boundary
of validity. Avoid adding redundant panels just to fill a rectangular grid.
A schematic communicates an interpretation, not independent measured evidence.

When adapting a gallery script, compare the required data meaning and structure
with what it actually plots. Reuse its layout only when compatible; otherwise
retain the useful composition idea and rebuild the calculation from the project
inputs. Record column-to-variable mappings, category order, units, and transforms.
Keep raw inputs unchanged and document exclusions and before/after counts.

Distinguish individual observations from aggregates, paired data from unrelated
groups, and independent samples from repeated measurements. An uncertainty band
needs an established definition (for example SD, SEM, confidence interval, or a
model interval). If that definition or sample unit is missing, resolve it before
adding statistical annotations. Do not derive significance from appearance.

## Choose a visual encoding

| Scientific task | Useful starting point | Check before using it |
| --- | --- | --- |
| Evolution with time/parameter | Curves or points | Sampling, gaps, monotonic x, units; smoothing is a transform |
| Group differences | Points/distributions and justified summaries | Sample unit, pairing, uncertainty definition |
| Effect with uncertainty | Estimates and intervals | Reference value, interval meaning, consistent scale |
| Spatial or matrix structure | Image/heat map with a scale | Extent, origin, aspect ratio, units, colour normalization |
| Mechanism or workflow | Native shapes or a suite producer | Meaning of each connection and what is schematic |

Use shared limits and colour scales for direct comparisons unless an explicit
reason calls for different ones. Bars encode lengths from a baseline; don't
truncate them just to amplify differences. If an expanded range is needed,
consider a point/interval plot and label the scale clearly. Keep full uncertainty
extents visible. A reference figure supplies no missing numerical data.

For diagrams, identify entities and relations before routing arrows. Distinguish
causation, data flow, sequence, and physical coupling. Use the project's style
and a legend where necessary; arrow direction is a scientific choice. Keep
connectors clear of text and inspect layer ordering at intersections.

## Inspect the final artifacts

Review both the complete composition and each panel. Check:

- Values, units, category order, axis transformations, and scale limits against
  the source. Verify a few plotted values or extrema independently of rendering.
- Error bands, markers, and significance labels against their stated meanings.
- Mathematical symbols, minus signs, subscripts, and glyph substitutions in the
  actual PDF/PNG, not only the source SVG or plotting window.
- Intended frame alignments, panel-letter anchors, and repeated spacing at the
  final physical size. Unequal spans and insets can be intentional.
- Labels, legends, and colour bars for overlap or clipping. Reserve a legend
  region when necessary instead of covering data. Check contrast and whether
  categories remain distinguishable without colour alone; use the theme's
  permitted markers, line styles, or hatching when helpful.

Keep automated and visual outcomes separate. A short review record can state
which exports were inspected, the preflight result, intentional exceptions,
and unresolved issues. Never report visual review as passed solely because a
renderer exited successfully. If correcting a defect, change the relevant
layout/style/input handling and rerun the affected checks.

Deliver enough provenance to rebuild each panel: input locations, computation,
filtering, and uncertainty definitions. A compact source-data table is useful
when those values are not already accessible in project outputs; avoid needless
duplication of large or sensitive datasets. State illustrative status in source
and accompanying description, rather than letting a polished render imply data.
