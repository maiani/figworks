---
name: figworks
description: Create, revise, render, and inspect editable scientific figures with FigWorks, combining plots, equations, schematics, and annotations. Use for figure authoring in research projects; library maintenance follows the repository's contributor guidance.
---

# FigWorks figure authoring

Produce figures that can be regenerated from Python and edited as SVG. This
workflow uses ordinary files, Python, and image inspection; it requires no
particular agent, tool API, provider, or harness.

This bundle targets FigWorks 0.10 APIs. Resolve `assets/` and `references/` paths
relative to this file, even when the research project is elsewhere. Keep the
folder together when copying it. A harness with skill discovery can load it as
usual; otherwise ask the agent to read this file directly. For example:

> Read `path/to/figworks/SKILL.md`. Use the project's data and style to revise
> `figures/response.py`, preserving its model, and export SVG/PDF plus a preview.

## Establish what the figure must communicate

Read project instructions, existing generators, nearby figures, and `style.md`.
Establish the scientific question, source data or model, audience, physical
size, and requested formats. Use decisions already made in the project; ask
only for missing choices that affect scientific meaning or the deliverable.

For a new or substantially reorganized figure, outline each panel's purpose and
input before drawing. Use [planning-and-review.md](references/planning-and-review.md)
for data mapping, chart choice, diagram semantics, and review. A small edit needs
only its relevant checks; do not force a planning document or approval round.

Preserve assumptions, units, normalization, and uncertainty. Keep measured data,
model predictions, and explanatory schematics distinguishable. Do not invent
results, error bars, or significance to finish a layout. Label illustrative data
and seed stochastic examples. Preserve the meaning of colours across figures.

## Build the editable source

Use the project's Python environment and inspect its installed FigWorks version.
For setup or export failures, read [environment.md](references/environment.md).
Do not assume this bundle lives inside a library checkout.

For a new generator, copy [figure.py](assets/figure.py) into the research project
and replace its explicitly illustrative model. For revisions, update the
existing generator. Keep scientific calculations and input paths inspectable.

- Compose with FigWorks; use Matplotlib for plots, VecTeX for TeX, VecView for
  projected 3D geometry, and VecWire for circuits as needed. Simple annotations
  can use native shapes. Producers integrate through `to_svg_document()`.
- Read both the tokens and prose of the project's theme. Visual choices belong
  in `style.md` or explicit caller configuration: the skill imposes no fixed
  palette, font, panel-letter format, dimensions, or journal look. Demo layout
  values are editable inputs, not design requirements.
- Keep the Matplotlib theme active during creation and placement, because math
  fonts may be selected at draw time. Read [composition.md](references/composition.md)
  for shared producer styles, equations, slots, definitions, and imported SVG.
- Use physical units. Bare FigWorks layout coordinates are pixels, whereas
  bare style-token lengths are points. Prefer explicit `mm` and `pt` at these
  boundaries.
- Give content meaningful IDs and Matplotlib artists `set_gid` identifiers.
  Panel names only identify layout regions; `add(..., id=...)` creates the
  selectable placement group. Keep identifiers stable across revisions.
- For aligned plot frames and preserved text sizes, pair `panel.subplots()`
  with `panel.add(..., fit="axes")`. Reserve space for labels outside the frame;
  the grid does not measure these overhangs. Do not move that frame afterwards
  with `tight_layout` or constrained layout.
- `fit="content"` scales typography with the drawing. Use `fit="none"` for
  physical-size content or scene slots for labels that keep their size.
  Choose a placement mode deliberately rather than shrinking text to hide a
  layout problem.

Use project-relative or generator-relative paths, deterministic ordering, and
semantic colours from the theme. Raster source data can remain raster; wrapping
it in SVG does not make it vector. Reference images can inform composition,
not supply unverified measurements or a substitute for the scientific model.

## Check, render, and revise

Run `figure.check(target=...)` on the assembled figure for the intended export.
Inspect errors, warnings, and `report.unchecked`. `report.ok` means only that no
errors were reported; `save()` does not run preflight. Default thresholds are
heuristics, not journal acceptance criteria.

Export requested files and a PNG preview. Inspect the rendered figure using the
environment's image/document viewer, including a rendered PDF when PDF is a
deliverable. Review both the complete page at intended size and dense panels in
detail. Follow the review reference for values, symbols, overlap, clipping,
contrast, and uncertainty. Automated checks do not establish scientific
correctness or detect every visual defect. If image inspection is unavailable,
report visual review as outstanding rather than claiming it passed.

Fix diagnosed problems in the generator and rerender. Keep changes focused;
if a problem persists, explain the concrete limitation instead of cycling through
unrelated redesigns. Do not suppress font checks or outline all text to hide a
missing font. Default math export selectively outlines unsupported math runs;
ordinary text remains editable.

For reproducibility-sensitive work, repeat the build in the same environment
and compare bytes. Record package, renderer, and font versions when archiving;
identity across different environments is not promised.

Deliver the generator, input locations, editable SVG, requested exports, and
regeneration command. Distinguish automated results from visual review and list
remaining findings. Keep manual SVG edits distinct from generator changes.

External workflow ideas and their scope are recorded in
[sources.md](references/sources.md); no external skill is required at runtime.
