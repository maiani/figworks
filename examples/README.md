# Examples

## Gallery

Journal figures from across the sciences, each one self-contained script that
writes SVG, PDF, and PNG to `out/` at its printed size (183 mm, Nature's
two-column width). Every figure pairs a schematic with quantitative panels
computed from the model it illustrates. Data shown as measurements are
simulated with fixed seeds, so every run is byte-identical.

| Script | Field | Figure |
| --- | --- | --- |
| `transmon_figure.py` | Superconducting qubits | device, circuit, potential, charge dispersion |
| `graphene_bands.py` | Condensed matter | honeycomb lattice, Dirac cones, bands, density of states |
| `microring_resonator.py` | Photonics | ring and bus waveguide, resonance comb, coupling regimes |
| `optical_tweezers.py` | Biophysics | DNA between trapped beads, force-extension, trap calibration |
| `hodgkin_huxley.py` | Neuroscience | ion channels, spikes, conductances, firing threshold |
| `exoplanet_transit.py` | Astrophysics | transit geometry, light curve, transmission spectrum |
| `energy_landscape.py` | Chemistry | potential-energy surface, minimum-energy path, barriers |

They need VecView and a TeX installation; the transmon also needs VecWire.
`gallery.py` builds them all, runs the publication preflight on each SVG, and
writes `out/gallery-report.json`; `--docs` also refreshes the documentation
gallery.

```bash
python examples/gallery.py
python examples/gallery.py --docs
```

## Workflows

Two scripts show workflows rather than figures, with core dependencies only:

- `publication_preflight.py` builds a deliberately flawed figure and prints its
  preflight report.
- `thesis_plots.py` is a figure collection: many figures from one registry, in
  one shared style (`thesis_style.md`).
