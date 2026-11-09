# Workflow sources and adaptation notes

Reviewed 2026-11-09, starting from the
[Tosea survey](https://tosea.ai/blog/scientific-figure-skills-researchers).
The survey is discovery material; the repository instructions informed the
choices below. Upstream runtime behavior was not independently benchmarked.

- [nature-figure](https://github.com/Yuan1z0825/nature-skills/tree/b6ae2cac022f4aac094d50f2938a3474ba315fbc/skills/nature-figure): explicit panel purpose, source mapping, adaptation checks, and review of final artifacts. FigWorks applies these through concise planning guidance and its existing preflight. It does not import backend-selection gates, journal-specific rules, or an image-generation provider.
- [figures4papers](https://github.com/ChenLiu-1996/figures4papers/tree/b709de17da7e8f9a72e51a5de5bced924a01eeab/scientific-figure-making): inspectable examples, optional references, and deliberate legend space. The FigWorks gallery remains the example source; typography and palettes stay in the project theme. Axis choices preserve the meaning of the marks rather than automatically tightening every range.
- [fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph/tree/1ca1ff9cfcb67893a43d32b9ef3a1b782c44a46f): distinct automated and visual review outcomes, and focused corrections after rendering. FigWorks uses that distinction without claiming an automatic overlap detector or prescribing a fixed number of iterations.
- [Excalidraw diagram skill](https://github.com/github/awesome-copilot/tree/main/skills/excalidraw-diagram-generator): explicit entities and typed relations before geometry. Here the editable representation is generated SVG with semantic IDs.
- [paper-figure-pptx](https://github.com/fengting124/paper-figure-pptx-skill): review the artifact rendered by the delivery backend and disclose missing validation capabilities. Here PDF/PNG inspection accompanies SVG generation; no presentation dependency is introduced.

The survey's framework-diagram, architecture, and image-generation repositories
also illustrate draft/review workflows, but their specialized output stacks do
not add a necessary FigWorks dependency.

This bundle contains original instructions and an original Python starter. No
external scripts, images, templates, or skill text are vendored. At review time,
[nature-skills](https://github.com/Yuan1z0825/nature-skills/blob/b6ae2cac022f4aac094d50f2938a3474ba315fbc/LICENSE)
carried Apache-2.0 and
[figures4papers](https://github.com/ChenLiu-1996/figures4papers/blob/b709de17da7e8f9a72e51a5de5bced924a01eeab/LICENSE)
carried CC BY-NC 4.0. Their licensing does not become FigWorks licensing through
these links; review the particular file's terms before any future code/asset reuse.
